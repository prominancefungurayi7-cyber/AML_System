-- PREPARED ONLY. Do not run without a separately approved, identity-guarded
-- disposable migration. This file never selects or modifies production aml.
CREATE TABLE v4_stage4s_disposable.v4_primary_attempt_events (
    event_id BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    transaction_id BIGINT NOT NULL,
    staff_user_id BIGINT NOT NULL,
    request_key CHAR(36) CHARACTER SET ascii COLLATE ascii_bin NOT NULL,
    event_kind VARCHAR(16) NOT NULL,
    recorded_at VARCHAR(40) NOT NULL,
    outcome VARCHAR(32) NOT NULL,
    error_code VARCHAR(64) NULL,
    result_body LONGTEXT NULL,
    reason VARCHAR(500) NULL,
    UNIQUE KEY uq_v4_attempt_event (transaction_id, request_key, event_kind),
    KEY idx_v4_attempt_staff (staff_user_id),
    CONSTRAINT fk_v4_attempt_transaction FOREIGN KEY (transaction_id)
        REFERENCES v4_stage4s_disposable.transactions(id),
    CONSTRAINT fk_v4_attempt_staff FOREIGN KEY (staff_user_id)
        REFERENCES v4_stage4s_disposable.users(id),
    CONSTRAINT ck_v4_attempt_kind CHECK (event_kind IN ('STARTED','COMPLETED','CLOSED')),
    CONSTRAINT ck_v4_attempt_outcome CHECK (
        (event_kind='STARTED' AND outcome='started' AND result_body IS NULL AND reason IS NULL) OR
        (event_kind='COMPLETED' AND outcome IN ('success','inference_error') AND result_body IS NOT NULL AND reason IS NULL) OR
        (event_kind='CLOSED' AND outcome='closed' AND result_body IS NULL AND reason IS NOT NULL)
    )
) ENGINE=InnoDB;

CREATE TRIGGER v4_stage4s_disposable.v4_retry_no_update
BEFORE UPDATE ON v4_stage4s_disposable.v4_primary_attempt_events
FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='V4 attempt audit is append-only';
CREATE TRIGGER v4_stage4s_disposable.v4_retry_no_delete
BEFORE DELETE ON v4_stage4s_disposable.v4_primary_attempt_events
FOR EACH ROW SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT='V4 attempt audit is append-only';
