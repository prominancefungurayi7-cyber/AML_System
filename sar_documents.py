"""Printable case documents delivered through authenticated private Messages."""
import hashlib
import io
import json
import uuid
from xml.sax.saxutils import escape


def document_record(conn, kind, identifier):
    if kind == 'sar':
        row = conn.execute('SELECT * FROM sar_reports WHERE id=?', (identifier,)).fetchone()
        if not row:
            raise LookupError('Report not found.')
        record = dict(row)
        record['title'] = 'Suspicious Activity Report'
        record['reference'] = record.get('reference_number') or f'SAR-{identifier}'
        record['author'] = record['filed_by']
    elif kind == 'escalation':
        row = conn.execute('SELECT * FROM alerts WHERE id=?', (identifier,)).fetchone()
        if not row or row['status'] != 'escalated':
            raise LookupError('Escalated case not found.')
        record = dict(row)
        record.update(title='Escalated Case Report', reference=f'CASE-{identifier}',
                      alert_id=identifier, narrative=record.get('case_notes') or '',
                      author=record.get('assigned_to') or '', created_at=record.get('timestamp'))
    else:
        raise ValueError('Unknown report type.')
    record['kind'] = kind
    return record


def render_pdf(record):
    from reportlab.lib.styles import getSampleStyleSheet
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
    styles = getSampleStyleSheet()
    styles['Normal'].fontName = 'Times-Roman'
    styles['Normal'].fontSize = 11
    styles['Normal'].leading = 15
    styles['Title'].fontName = 'Times-Bold'
    stream = io.BytesIO()
    doc = SimpleDocTemplate(stream, pagesize=A4, rightMargin=48, leftMargin=48,
                            topMargin=48, bottomMargin=48,
                            title=record['title'], author='EpoCash AML', invariant=1)
    story = [Paragraph('EpoCash AML', styles['Title']),
             Paragraph(escape(record['title']), styles['Heading1'])]
    fields = [('Reference', record['reference']), ('Account', record['account_number']),
              ('Alert', record['alert_id']), ('Prepared by', record['author']),
              ('Status', record['status']), ('Created', record.get('created_at')),
              ('Submitted', record.get('filed_at'))]
    for label, value in fields:
        if value is not None:
            story.append(Paragraph(f'<b>{label}:</b> {escape(str(value))}', styles['Normal']))
    story += [Spacer(1, 12), Paragraph('Case narrative', styles['Heading2'])]
    for line in str(record.get('narrative') or '').splitlines():
        story.append(Paragraph(escape(line) or '&#160;', styles['Normal']))
    story += [Spacer(1, 18), Paragraph(
        'Confidential. Internal review and administrator handoff only. '
        'This document is not evidence of transmission to an external FIU.', styles['Normal'])]
    def page_number(canvas, doc):
        canvas.setFont('Times-Roman', 9)
        canvas.drawRightString(A4[0] - 48, 28, f'Page {doc.page}')
    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    return stream.getvalue()


def deliver_to_admins(conn, kind, identifier, sender, root, notify=None):
    """Retry safely after a failed response; no new tables or external sending.

    Deterministic document bytes and request identities use the existing
    conversation lock and attachment deduplication. Cases remain in Reports
    even when a storage/message failure requires a manual retry.
    """
    from werkzeug.datastructures import FileStorage
    from message_attachments import save_upload, encode_message, remove_upload
    from messaging import get_or_create_conversation, send_message
    if sender['role'] not in ('admin', 'compliance'):
        raise PermissionError('Staff access required.')
    record = document_record(conn, kind, identifier)
    admins = conn.execute("SELECT username FROM users WHERE role='admin' ORDER BY id").fetchall()
    if not admins:
        raise RuntimeError('No administrator account is available for document delivery.')
    content = render_pdf(record)
    identity = json.dumps([kind, identifier, record['status'], hashlib.sha256(content).hexdigest()])
    request_id = uuid.UUID(bytes=hashlib.sha256(identity.encode()).digest()[:16], version=4).hex
    caption = f"{record['title']} {record['reference']} - internal administrator review."
    results = []
    for admin in admins:
        if admin['username'] == sender['username']:
            continue  # The author already has Reports access; self-chats are forbidden.
        conversation = get_or_create_conversation(conn, sender['username'], admin['username'])
        metadata = save_upload(FileStorage(stream=io.BytesIO(content), filename=f'{record["reference"]}.pdf'),
                               root, uuid.uuid4().hex)
        metadata['request_id'] = request_id
        # Preserve the file on uncertain commit acknowledgement; a committed
        # message must never lose its document. Retrying uses the same key.
        message = send_message(conn, conversation['id'], sender['username'], admin['username'],
                               encode_message(caption, metadata), sender['role'],
                               attachment_request_id=request_id)
        if message.get('replayed'):
            remove_upload(root, metadata['id'])
        elif notify is not None:
            try:
                notify(message, conversation['id'])
            except Exception:
                pass  # Stored history is authoritative if realtime is offline.
        results.append(message)
    return results
