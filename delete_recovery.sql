-- Enhanced Delete Recovery Script
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
WHERE is_active = 0 
ORDER BY updated_at DESC;

-- Step 2: Recover specific student by ID
-- UPDATE students 
-- SET is_active = 1, deleted_at = NULL, updated_at = CURRENT_TIMESTAMP
-- WHERE student_id = ?;

-- Step 3: Recover all recently deleted (within last hour)
-- UPDATE students 
-- SET is_active = 1, deleted_at = NULL, updated_at = CURRENT_TIMESTAMP
-- WHERE is_active = 0 AND updated_at > datetime('now', '-1 hour');

-- Step 4: Permanent delete (use with extreme caution)
-- DELETE FROM students WHERE is_active = 0 AND deleted_at < datetime('now', '-30 days');
