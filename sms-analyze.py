import sqlite3
import re

phone_to_contact = {}
contacts_conn = sqlite3.connect('contacts_database-2015-08-31.sqlite3')
contacts_conn.row_factory = sqlite3.Row
contacts_db = contacts_conn.cursor()
contacts_db.execute('''
    SELECT
        ABPerson.First,
        ABPerson.Last,
        ABPerson.Organization,
        ABMultiValue.property,
        ABMultiValue.value,
        ABPerson.ROWID,
        ABMultiValue.UID,
        ABMultiValue.record_id
    FROM ABPerson JOIN ABMultiValue ON (ABPerson.ROWID = ABMultiValue.record_id);
''')

for row in contacts_db.fetchall():
    if row['property'] == 3:
        # Assert: this is a phone number record
        phone = re.sub(r'\D', "", row['value']) # Remove non-digits
        first = row['First']
        last = row['Last']
        organization = row['Organization']

        if first == None and last == None and organization != None:
            first = last = organization
        elif first == None and last == None:
            first = last = "UNKNOWN"

        first = first if first != None else ""
        last = last if last != None else ""

        if re.match(r'^1\d{10}$', phone):
            key = "+%s" % phone
        elif re.match(r'^\d{10}$', phone):
            key = "+1%s" % phone
        elif re.match(r'^331\d{4}$', phone):
            # An implicit 315 number. How quaint.
            key = "+1315%s" % phone
        else:
            key = "+%s" % phone

        phone_to_contact[key] = {"first": first, "last": last}

        # Python might try to encode these into ASCII unless we're deliberate
        # print("%s %s %s %s" % (first.encode('utf8'), last.encode('utf8'), phone.encode('utf8'), key.encode('utf8')))

messages_conn = sqlite3.connect('sms_database-2015-08-31.sqlite3')
messages_conn.row_factory = sqlite3.Row
messages_db = messages_conn.cursor()
messages_db.execute('''
    SELECT
        handle.ROWID,
        handle.id,
        message.other_handle,
        -- datetime(message.date + 978307200, 'unixepoch', 'localtime') AS 'time',
        message.text,
        message.is_from_me
    FROM message JOIN handle ON (message.handle_id = handle.ROWID)
    WHERE
        -- handle.ROWID IN (147, 186)
        -- time > DATE('2014-08-31')
        -- AND time < DATE('2015-08-31')
        datetime(message.date + 978307200, 'unixepoch', 'localtime') > DATE('2015-07-31')
        AND datetime(message.date + 978307200, 'unixepoch', 'localtime') < DATE('2015-08-31')
        -- AND message.is_from_me = 0
        AND handle.ROWID NOT IN (164, 419, 173, 384, 461, 17)
    ORDER BY message.date DESC
''')

for row in messages_db.fetchall():
    phone = row['id']
    text = row['text']
    arrow = "<-" if row['is_from_me'] else "->"

    if phone in phone_to_contact:
        first = phone_to_contact[phone]["first"]
        last = phone_to_contact[phone]["last"]

        if phone == None:
            phone = "unknown_number"
        if text == None:
            text = "NO_TEXT (image?)"

        print("%s %s %s %s" % (first.encode('utf8'), last.encode('utf8'), arrow, text.encode('utf8')))
    else:
        if phone == None:
            phone = "XX"
        if text == None:
            text = "NO_TEXT (image?)"

        print("Phone number %s does not have a contact %s" % (phone.encode('utf8'), text.encode('utf8')))
