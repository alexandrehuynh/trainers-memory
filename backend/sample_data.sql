-- Insert sample clients
INSERT INTO public.clients (id, name, email, phone, notes, created_at, updated_at)
VALUES 
  ('00000000-0000-0000-0000-000000000001', 'John Doe', 'john@example.com', '555-123-4567', 'Regular client since 2022', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000002', 'Jane Smith', 'jane@example.com', '555-987-6543', 'Prefers morning sessions', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000003', 'Alex Johnson', 'alex@example.com', '555-456-7890', 'Focus on rehabilitation', NOW(), NOW());

-- Insert sample workouts
INSERT INTO public.workouts (id, client_id, date, type, duration, notes, created_at, updated_at)
VALUES 
  ('00000000-0000-0000-0000-000000000011', '00000000-0000-0000-0000-000000000001', '2024-03-08 10:00:00', 'Strength Training', 60, 'Focused on upper body', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000012', '00000000-0000-0000-0000-000000000002', '2024-03-07 15:30:00', 'Cardio', 45, 'HIIT session', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000013', '00000000-0000-0000-0000-000000000003', '2024-03-06 09:00:00', 'Flexibility', 30, 'Yoga and stretching', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000014', '00000000-0000-0000-0000-000000000001', '2024-03-05 11:00:00', 'Core', 45, 'Focus on abs and lower back', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000015', '00000000-0000-0000-0000-000000000002', '2024-03-04 16:00:00', 'Endurance', 75, 'Long distance running prep', NOW(), NOW());

-- Insert sample exercises
INSERT INTO public.exercises (id, workout_id, name, sets, reps, weight, notes, created_at, updated_at)
VALUES 
  -- Exercises for John's Strength Training
  ('00000000-0000-0000-0000-000000000021', '00000000-0000-0000-0000-000000000011', 'Bench Press', 3, 10, 135.5, 'Increase weight next time', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000022', '00000000-0000-0000-0000-000000000011', 'Lat Pulldown', 3, 12, 120.0, NULL, NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000023', '00000000-0000-0000-0000-000000000011', 'Bicep Curls', 3, 12, 25.0, 'Slow reps', NOW(), NOW()),
  
  -- Exercises for Jane's Cardio
  ('00000000-0000-0000-0000-000000000024', '00000000-0000-0000-0000-000000000012', 'Treadmill Sprint', 5, 1, 0.0, '1 min sprint, 1 min rest', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000025', '00000000-0000-0000-0000-000000000012', 'Jumping Jacks', 3, 30, 0.0, NULL, NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000026', '00000000-0000-0000-0000-000000000012', 'Burpees', 3, 15, 0.0, 'Modified due to wrist pain', NOW(), NOW()),
  
  -- Exercises for Alex's Flexibility
  ('00000000-0000-0000-0000-000000000027', '00000000-0000-0000-0000-000000000013', 'Downward Dog', 1, 5, 0.0, 'Hold 30 seconds each', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000028', '00000000-0000-0000-0000-000000000013', 'Hamstring Stretch', 2, 4, 0.0, 'Hold 45 seconds each side', NOW(), NOW()),
  
  -- Exercises for John's Core workout
  ('00000000-0000-0000-0000-000000000029', '00000000-0000-0000-0000-000000000014', 'Crunches', 3, 20, 0.0, NULL, NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000030', '00000000-0000-0000-0000-000000000014', 'Plank', 3, 1, 0.0, 'Hold for 60 seconds', NOW(), NOW()),
  
  -- Exercises for Jane's Endurance
  ('00000000-0000-0000-0000-000000000031', '00000000-0000-0000-0000-000000000015', 'Distance Run', 1, 1, 0.0, '5km at steady pace', NOW(), NOW()),
  ('00000000-0000-0000-0000-000000000032', '00000000-0000-0000-0000-000000000015', 'Cool Down Walk', 1, 1, 0.0, '10 minutes', NOW(), NOW());

-- Insert a test API key with client_id (the foreign key relationship requires this)
INSERT INTO public.api_keys (id, key, client_id, name, description, active, created_at)
VALUES ('00000000-0000-0000-0000-000000000099', 'test_key_12345', '00000000-0000-0000-0000-000000000001', 'Test API Key', 'For development and testing', true, NOW()); 