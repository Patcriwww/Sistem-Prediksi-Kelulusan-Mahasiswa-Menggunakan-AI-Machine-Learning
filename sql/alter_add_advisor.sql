-- add advisor_id to students table (Postgres)
ALTER TABLE students
  ADD COLUMN IF NOT EXISTS advisor_id INT;

-- try to add FK constraint (use a name that won't conflict)
DO $$
BEGIN
  IF NOT EXISTS (
    SELECT 1
    FROM information_schema.table_constraints tc
    JOIN information_schema.key_column_usage kcu
      ON tc.constraint_name = kcu.constraint_name
    WHERE tc.table_name = 'students'
      AND tc.constraint_type = 'FOREIGN KEY'
      AND kcu.column_name = 'advisor_id'
  ) THEN
    ALTER TABLE students
      ADD CONSTRAINT fk_students_advisor FOREIGN KEY (advisor_id) REFERENCES users(id) ON DELETE SET NULL;
  END IF;
END$$;

-- add index
CREATE INDEX IF NOT EXISTS idx_students_advisor ON students(advisor_id);
