-- Test Data for EvelinaAI Database
-- Lithuanian Cancer Patients and Related Data

-- Create test doctors first
INSERT INTO evelinaai.users (id, email, phone, created_at, last_active, preferred_language, subsidy_eligible, legal_consents, support_status) VALUES
('11123c45-6789-0abc-def1-234567890abc', 'dr.jonas.kazlauskas@hospital.lt', '+37061234567', NOW(), NOW(), 'lt', false, '{"privacy": true, "terms": true}', 'active'),
('11234d56-789a-bcde-f123-4567890abcd1', 'dr.egle.paulauskiene@hospital.lt', '+37061234568', NOW(), NOW(), 'lt', false, '{"privacy": true, "terms": true}', 'active');

-- Create 10 Lithuanian cancer patients
INSERT INTO evelinaai.users (id, email, phone, created_at, last_active, preferred_language, subsidy_eligible, legal_consents, support_status) VALUES
('21a23b45-6789-0abc-def1-234567890abc', 'petras.kazlauskas@gmail.com', '+37061234501', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active'),
('22b34c56-789a-bcde-f123-4567890abcd1', 'ona.petraitiene@gmail.com', '+37061234502', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active'),
('23c45d67-89ab-cdef-1234-567890abcde2', 'jonas.butkus@gmail.com', '+37061234503', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active'),
('24d56e78-9abc-def1-2345-67890abcdef3', 'marija.pauliene@gmail.com', '+37061234504', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active'),
('25e67f89-abcd-ef12-3456-7890abcdef04', 'antanas.kazlauskas@gmail.com', '+37061234505', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active'),
('26f78a90-bcde-f123-4567-890abcdef015', 'birute.matuleviciene@gmail.com', '+37061234506', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active'),
('27a89b01-cdef-1234-5678-90abcdef0126', 'vytautas.jonaitis@gmail.com', '+37061234507', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active'),
('28a90b12-def1-2345-6789-0abcdef01237', 'aldona.stankeviciene@gmail.com', '+37061234508', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active'),
('29a01b23-ef12-3456-789a-bcdef0123458', 'rimas.petrauskas@gmail.com', '+37061234509', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active'),
('20a12b34-f123-4567-89ab-cdef01234569', 'daiva.butkiene@gmail.com', '+37061234510', NOW(), NOW(), 'lt', true, '{"privacy": true, "terms": true}', 'active');

-- Create risk assessments for patients
INSERT INTO evelinaai.risk_assessments (id, user_id, risk_type, risk_level, detected_at, trigger_criteria, anonymized_flag) VALUES
('31a23b45-6789-0abc-def1-234567890abc', '21a23b45-6789-0abc-def1-234567890abc', 'support', 'high', NOW(), 'Severe symptoms reported', false),
('32b34c56-789a-bcde-f123-4567890abcd1', '22b34c56-789a-bcde-f123-4567890abcd1', 'support', 'medium', NOW(), 'Moderate symptoms, responding to treatment', false),
('33c45d67-89ab-cdef-1234-567890abcde2', '23c45d67-89ab-cdef-1234-567890abcde2', 'support', 'high', NOW(), 'Advanced stage cancer', false),
('34d56e78-9abc-def1-2345-67890abcdef3', '24d56e78-9abc-def1-2345-67890abcdef3', 'support', 'medium', NOW(), 'Post-surgery monitoring', false),
('35e67f89-abcd-ef12-3456-7890abcdef04', '25e67f89-abcd-ef12-3456-7890abcdef04', 'support', 'high', NOW(), 'Critical condition', false);

-- Create scheduled appointments
INSERT INTO evelinaai.scheduled_appointments (id, user_id, scheduled_time, contact_method, purpose, status) VALUES
('41a23b45-6789-0abc-def1-234567890abc', '21a23b45-6789-0abc-def1-234567890abc', NOW() + INTERVAL '2 days', 'sms', 'support_checkin', 'pending'),
('42b34c56-789a-bcde-f123-4567890abcd1', '22b34c56-789a-bcde-f123-4567890abcd1', NOW() + INTERVAL '3 days', 'email', 'support_checkin', 'pending'),
('43c45d67-89ab-cdef-1234-567890abcde2', '23c45d67-89ab-cdef-1234-567890abcde2', NOW() + INTERVAL '1 day', 'push', 'support_checkin', 'pending');

-- Create conversations
INSERT INTO evelinaai.conversations (id, user_id, platform, start_time, end_time, conversation_type, status) VALUES
('51a23b45-6789-0abc-def1-234567890abc', '21a23b45-6789-0abc-def1-234567890abc', 'telegram', NOW(), NULL, 'support', 'active'),
('52b34c56-789a-bcde-f123-4567890abcd1', '21a23b45-6789-0abc-def1-234567890abc', 'whatsapp', NOW(), NULL, 'support', 'active'),
('53c45d67-89ab-cdef-1234-567890abcde2', '22b34c56-789a-bcde-f123-4567890abcd1', 'chainlit', NOW(), NULL, 'support', 'active');

-- Create conversation details
INSERT INTO evelinaai.conversation_details (id, conversation_id, message_content, message_type, sent_at, sender, metadata) VALUES
('61a23b45-6789-0abc-def1-234567890abc', '51a23b45-6789-0abc-def1-234567890abc', 'Jaučiu stiprų skausmą krūtinėje ir sunkiai kvėpuoju.', 'text', NOW(), 'user', '{"severity": "high"}'),
('62b34c56-789a-bcde-f123-4567890abcd1', '51a23b45-6789-0abc-def1-234567890abc', 'Suprantu, kad jaučiatės blogai. Ar galite tiksliau apibūdinti skausmo pobūdį?', 'text', NOW(), 'evelina', '{"intent": "symptom_clarification"}'),
('63c45d67-89ab-cdef-1234-567890abcde2', '51a23b45-6789-0abc-def1-234567890abc', 'Skausmas aštrus, ypač įkvepiant.', 'text', NOW(), 'user', '{"severity": "high"}'),
('64d56e78-89ab-cdef-1234-567890abcde2', '51a23b45-6789-0abc-def1-234567890abc', 'Dėl šių simptomų būtina skubi konsultacija. Organizuoju skubų vizitą.', 'text', NOW(), 'evelina', '{"action": "schedule_urgent_appointment"}');

-- Create reports
INSERT INTO evelinaai.reports (id, generated_by, report_type, report_format, storage_path, parameters) VALUES
('71a23b45-6789-0abc-def1-234567890abc', '11123c45-6789-0abc-def1-234567890abc', 'interaction', 'pdf', '/reports/interactions/2024/03/report1.pdf', '{"period": "2024-03", "type": "monthly"}'),
('72b34c56-789a-bcde-f123-4567890abcd1', '11234d56-789a-bcde-f123-4567890abcd1', 'usage', 'json', '/reports/usage/2024/03/report2.json', '{"period": "2024-03", "type": "monthly"}');

-- Create memory entries
INSERT INTO evelinaai.long_term_memory (id, user_id, memory_type, content, recorded_at) VALUES
('81a23b45-6789-0abc-def1-234567890abc', '21a23b45-6789-0abc-def1-234567890abc', 'interaction_pattern', 
  '{"pattern": "frequent_pain_reports", "details": "Patient consistently reports chest pain during breathing"}', NOW()),
('82b34c56-789a-bcde-f123-4567890abcd1', '22b34c56-789a-bcde-f123-4567890abcd1', 'preference',
  '{"communication": "prefers_morning_contact", "language": "formal_lithuanian"}', NOW());

INSERT INTO evelinaai.short_term_memory (id, user_id, conversation_id, context, expires_at) VALUES
('91a23b45-6789-0abc-def1-234567890abc', '21a23b45-6789-0abc-def1-234567890abc', '51a23b45-6789-0abc-def1-234567890abc',
  '{"current_topic": "chest_pain", "severity": "high", "last_action": "scheduling_appointment"}', NOW() + INTERVAL '30 minutes'),
('92b34c56-789a-bcde-f123-4567890abcd1', '22b34c56-789a-bcde-f123-4567890abcd1', '53c45d67-89ab-cdef-1234-567890abcde2',
  '{"current_topic": "treatment_discussion", "last_action": "explaining_options"}', NOW() + INTERVAL '30 minutes');

-- Add some completed appointments for history
INSERT INTO evelinaai.scheduled_appointments (id, user_id, scheduled_time, contact_method, purpose, status) VALUES
('a1a23b45-6789-0abc-def1-234567890abc', '21a23b45-6789-0abc-def1-234567890abc', NOW() - INTERVAL '7 days', 'sms', 'support_checkin', 'completed'),
('a2b34c56-789a-bcde-f123-4567890abcd1', '22b34c56-789a-bcde-f123-4567890abcd1', NOW() - INTERVAL '14 days', 'email', 'support_checkin', 'completed');

-- Add follow-up risk assessments
INSERT INTO evelinaai.risk_assessments (id, user_id, risk_type, risk_level, detected_at, trigger_criteria, anonymized_flag) VALUES
('b1a23b45-6789-0abc-def1-234567890abc', '21a23b45-6789-0abc-def1-234567890abc', 'support', 'high', NOW() - INTERVAL '7 days', 'Condition stable but critical', false),
('b2b34c56-789a-bcde-f123-4567890abcd1', '22b34c56-789a-bcde-f123-4567890abcd1', 'support', 'medium', NOW() - INTERVAL '14 days', 'Showing improvement after treatment', false); 