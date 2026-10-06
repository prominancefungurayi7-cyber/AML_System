-- ADMINISTRATOR HANDOFF ONLY. Not executed by this file.
-- Select the same application database explicitly before using.
-- Install via an authorized migration identity; do not weaken binary logging.
-- The restricted CLI must verify all definitions before any boundary is established.
DELIMITER $$
CREATE TRIGGER cmm_tx_insert AFTER INSERT ON transactions FOR EACH ROW BEGIN INSERT INTO cmm_source_changes (transaction_id,operation,event_timestamp,recorded_at) VALUES (NEW.id,'SOURCE_INSERT',NEW.timestamp,DATE_FORMAT(UTC_TIMESTAMP(6),'%Y-%m-%dT%H:%i:%s.%fZ')); END$$
CREATE TRIGGER cmm_tx_update AFTER UPDATE ON transactions FOR EACH ROW BEGIN IF NOT (OLD.id <=> NEW.id AND OLD.timestamp <=> NEW.timestamp AND OLD.sender_account <=> NEW.sender_account AND OLD.receiver_account <=> NEW.receiver_account AND OLD.transaction_type <=> NEW.transaction_type AND OLD.currency <=> NEW.currency AND OLD.agent_id <=> NEW.agent_id AND OLD.amount <=> NEW.amount) THEN INSERT INTO cmm_source_changes (transaction_id,operation,event_timestamp,recorded_at) VALUES (NEW.id,'SOURCE_UPDATE',NEW.timestamp,DATE_FORMAT(UTC_TIMESTAMP(6),'%Y-%m-%dT%H:%i:%s.%fZ')); END IF; END$$
CREATE TRIGGER cmm_tx_delete AFTER DELETE ON transactions FOR EACH ROW BEGIN INSERT INTO cmm_source_changes (transaction_id,operation,event_timestamp,recorded_at) VALUES (OLD.id,'SOURCE_DELETE',OLD.timestamp,DATE_FORMAT(UTC_TIMESTAMP(6),'%Y-%m-%dT%H:%i:%s.%fZ')); END$$
CREATE TRIGGER cmm_ce_insert AFTER INSERT ON canonical_mobile_money_events FOR EACH ROW BEGIN INSERT INTO cmm_source_changes (transaction_id,operation,event_timestamp,recorded_at) VALUES (NEW.transaction_id,'CANONICAL_INSERT',NEW.event_timestamp,DATE_FORMAT(UTC_TIMESTAMP(6),'%Y-%m-%dT%H:%i:%s.%fZ')); END$$
CREATE TRIGGER cmm_ce_update AFTER UPDATE ON canonical_mobile_money_events FOR EACH ROW BEGIN INSERT INTO cmm_source_changes (transaction_id,operation,event_timestamp,recorded_at) VALUES (NEW.transaction_id,'CANONICAL_UPDATE',NEW.event_timestamp,DATE_FORMAT(UTC_TIMESTAMP(6),'%Y-%m-%dT%H:%i:%s.%fZ')); END$$
CREATE TRIGGER cmm_ce_delete AFTER DELETE ON canonical_mobile_money_events FOR EACH ROW BEGIN INSERT INTO cmm_source_changes (transaction_id,operation,event_timestamp,recorded_at) VALUES (OLD.transaction_id,'CANONICAL_DELETE',OLD.event_timestamp,DATE_FORMAT(UTC_TIMESTAMP(6),'%Y-%m-%dT%H:%i:%s.%fZ')); END$$
DELIMITER ;
