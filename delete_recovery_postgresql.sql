-- Enhanced Delete Recovery Script for PostgreSQL
-- Use this to recover accidentally deleted students

-- Step 1: View recently deleted students
SELECT 
    student_id, 
    name, 
    class_name, 
    section,
    deleted_at,
    updated_at
FROM students 
WHERE is_active = false 
ORDER BY updated_at DESC;

-- Step 2: Recover specific student by ID
-- UPDATE students 
-- SET is_active = true, deleted_at = NULL, updated_at = CURRENT_TIMESTAMP
-- WHERE student_id = $1;

-- Step 3: Recover all recently deleted (within last hour)
-- UPDATE students 
-- SET is_active = true, deleted_at = NULL, updated_at = CURRENT_TIMESTAMP
-- WHERE is_active = false AND updated_at > NOW() - INTERVAL '1 hour';

-- Step 4: Permanent delete (use with extreme caution)
-- DELETE FROM students WHERE is_active = false AND deleted_at < NOW() - INTERVAL '30 days';
