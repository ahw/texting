import sqlite3
import re
import hashlib

def raw_to_canonical_phone(value):
    phone_digits_only = re.sub(r'\D', "", value) # Remove non-digits

    if re.match(r'^\d{10}\d+$', phone_digits_only):
        # Assert: phone number is > 10 digits (country code already exists)
        return "+" + phone_digits_only
    elif re.match(r'^\d{10}$', phone_digits_only):
        # Assert: phone number exactly 10 digits. Implied U.S. number
        return "+1" + phone_digits_only
    elif re.match(r'^331\d{4}$', phone_digits_only):
        # Assert: an old Newark 331 number. Implied U.S. 315 area code
        return "+1315" + phone_digits_only
    else:
        # Assert: some sort of weird invalid number. Do nothing.
        return phone_digits_only



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

contacts = {}
contact_phone_canonical_index = {}
contact_email_index = {}

for row in contacts_db.fetchall():
    record_id = row['record_id']
    value = row['value']

    if not record_id in contacts:
        contacts[record_id] = {}

    if row['property'] == 3:
        # Assert: this is a phone number record
        phone_digits_only = re.sub(r'\D', "", value) # Remove non-digits

        phone_canonical = raw_to_canonical_phone(value)

        sha = hashlib.sha1()
        sha.update(phone_canonical)
        phone_hash = sha.hexdigest()
        contacts[record_id]["phone_raw"] = value
        contacts[record_id]["phone_digits_only"] = phone_digits_only
        contacts[record_id]["phone_canonical"] = phone_canonical
        contacts[record_id]["phone_hash"] = phone_hash
        contact_phone_canonical_index[phone_canonical] = contacts[record_id]
        print("Setting phone index \"%s\" -> %s" % (phone_canonical, record_id))

    elif row['property'] == 4:
        # Assert: this is an email record
        contacts[record_id]["email"] = value
        contact_email_index[value] = contacts[record_id]
        print("Setting email index \"%s\" -> %s" % (value.encode('utf8'), record_id))

    else:
        # Return early, we don't care about non-email or non-phone records.
        # This could be a record for Facebook, mailing address, etc.
        continue

    first = row['First'] if row['First'] != None else ""
    last = row['Last'] if row['Last'] != None else ""
    organization = row['Organization'] if row['Organization'] != None else ""

    contacts[record_id]["first"] = first
    contacts[record_id]["last"] = last
    contacts[record_id]["organization"] = organization

    print("\tFirst: %s\n\tLast: %s\n\tOrg: %s" % \
        (contacts[record_id]["first"].encode('utf8'), \
        contacts[record_id]["last"].encode('utf8'), \
        contacts[record_id]["organization"].encode('utf8')))


    # if re.match(r'^1\d{10}$', phone):
    #     # U.S. number - country code 1
    #     key = "+%s" % phone
    # elif re.match(r'^\d{10}$', phone):
    #     # No country code, assume U.S.
    #     key = "+1%s" % phone
    # elif re.match(r'^331\d{4}$', phone):
    #     # An implicit 315 number. How quaint.
    #     key = "+1315%s" % phone
    # else:
    #     # Anything else. International number, invalid phone numbers, etc.
    #     key = "+%s" % phone

    # phone_to_contact[key] = {"first": first, "last": last, "phone_hash": phone_hash}

    # Python might try to encode these into ASCII unless we're deliberate
    # print("\"%s %s\" %s %s" % \
    #     (first.encode('utf8'), \
    #     last.encode('utf8'), \
    #     phone.encode('utf8'), \
    #     key.encode('utf8')))

print(contact_phone_canonical_index)
print(contact_email_index)

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
        datetime(message.date + 978307200, 'unixepoch', 'localtime') > DATE('2010-07-31')
        AND datetime(message.date + 978307200, 'unixepoch', 'localtime') < DATE('2015-08-31')
        -- AND message.is_from_me = 0
        -- AND handle.ROWID NOT IN (164, 419, 173, 384, 461, 17)
    ORDER BY message.date DESC
''')

for row in messages_db.fetchall():
    contact_id = row['id']
    text = row['text']
    arrow = "<-" if row['is_from_me'] else "->"
    # try:
    #     phone_hash = phone_to_contact[phone]["phone_hash"]
    # except KeyError:
    #     print("Error!")
    #     print(phone)

    if contact_id in contact_phone_canonical_index:
        print("HIT %s in contact_phone_canonical_index" % contact_id)
    elif contact_id in contact_email_index:
        print("HIT %s in contact_email_index" % contact_id)
    else:
        print("MISS %s in either index" % contact_id)
        if text != None:
            print("\t text was %s" % text.encode('utf8'))

    # first,last = [phone_to_contact[phone][k] for k in ('first','last')]

    # if text == None:
    #     text = "NO_TEXT (image?)"
    # else:
    #     if phone == None:
    #         phone = "XX"
    #     if text == None:
    #         text = "NO_TEXT (image?)"


    # print("%s %s (%s) [%s] %s %s" % \
    #     (first.encode('utf8'), \
    #     last.encode('utf8'), \
    #     phone_hash, \
    #     phone.encode('utf8'), \
    #     arrow, \
    #     text.encode('utf8')))
    #     print("Phone number %s does not have a contact %s" % (phone.encode('utf8'), text.encode('utf8')))
