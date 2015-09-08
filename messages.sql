.mode csv
.headers ON

-- To figure out a contact's ROWID use something like
-- SELECT * FROM handle WHERE id LIKE "+1234567890"

SELECT
    handle.ROWID,
    -- datetime(message.date + 978307200, 'unixepoch', 'localtime') AS 'time',
    message.text
    -- message.is_from_me
FROM message JOIN handle ON (message.handle_id = handle.ROWID)
WHERE
    -- handle.ROWID IN (147, 186)
    -- time > DATE('2014-08-31')
    -- AND time < DATE('2015-08-31')
    datetime(message.date + 978307200, 'unixepoch', 'localtime') > DATE('2014-08-31')
    AND datetime(message.date + 978307200, 'unixepoch', 'localtime') < DATE('2015-08-31')
    -- AND message.is_from_me = 0
    AND handle.ROWID NOT IN (164, 419, 173, 384, 461, 17)
ORDER BY message.date DESC;

.exit
