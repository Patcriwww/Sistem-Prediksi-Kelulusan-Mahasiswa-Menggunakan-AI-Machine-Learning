-- Add fakultas and kelas tables and kelas_code column on students (safe for existing DBs)

CREATE TABLE IF NOT EXISTS fakultas (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255),
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

CREATE TABLE IF NOT EXISTS kelas (
    id SERIAL PRIMARY KEY,
    code VARCHAR(50) UNIQUE NOT NULL,
    name VARCHAR(255),
    fakultas_id INT,
    created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now()
);

-- Add FK from kelas to fakultas if the column exists and FK not defined
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_kelas_fakultas') THEN
        ALTER TABLE kelas ADD CONSTRAINT fk_kelas_fakultas FOREIGN KEY (fakultas_id) REFERENCES fakultas(id) ON DELETE SET NULL;
    END IF;
END$$;

-- Add kelas_code to students if not exists
ALTER TABLE students ADD COLUMN IF NOT EXISTS kelas_code INT;

-- Create index and FK for students.kelas_code if not exists
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_constraint WHERE conname = 'fk_students_kelas') THEN
        ALTER TABLE students ADD CONSTRAINT fk_students_kelas FOREIGN KEY (kelas_code) REFERENCES kelas(id) ON DELETE SET NULL;
    END IF;
END$$;

CREATE INDEX IF NOT EXISTS idx_students_kelas ON students(kelas_code);
