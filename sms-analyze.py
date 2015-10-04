import sqlite3
import re
import hashlib
import json
import matplotlib.pyplot as plot
from datetime import datetime, date, time

try:
    conf_file = open('config.json', 'r')
    config = json.load(conf_file)
except IOError:
    print("Could not open file")
    config = None

def myprint(value):
    # print(value)
    return

# Turn a poorly-formatted phone number into it's canonical format:
# [+] + [country code] + [area code] + [local number]
#
# Example: +15551234567
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
        # print("Setting phone index \"%s\" -> %s" % (phone_canonical, record_id))

    elif row['property'] == 4:
        # Assert: this is an email record
        contacts[record_id]["email"] = value
        contact_email_index[value] = contacts[record_id]
        # print("Setting email index \"%s\" -> %s" % (value.encode('utf8'), record_id))

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

    # print("\tFirst: %s\n\tLast: %s\n\tOrg: %s" % \
    #     (contacts[record_id]["first"].encode('utf8'), \
    #     contacts[record_id]["last"].encode('utf8'), \
    #     contacts[record_id]["organization"].encode('utf8')))


messages_conn = sqlite3.connect('sms_database-2015-08-31.sqlite3')
messages_conn.row_factory = sqlite3.Row
messages_db = messages_conn.cursor()
messages_db.execute('''
    SELECT
        handle.ROWID,
        handle.id,
        message.other_handle,
        datetime(message.date + 978307200, 'unixepoch', 'localtime') AS 'time',
        message.text,
        message.is_from_me
    FROM message JOIN handle ON (message.handle_id = handle.ROWID)
    WHERE
        -- handle.ROWID IN (?)
        -- handle.ROWID IN (147, 186)
        -- time > DATE('2014-08-31')
        -- AND time < DATE('2015-08-31')
        datetime(message.date + 978307200, 'unixepoch', 'localtime') > DATE('2010-07-31')
        AND datetime(message.date + 978307200, 'unixepoch', 'localtime') < DATE('2015-08-31')
        -- AND message.is_from_me = 0
        -- AND handle.ROWID NOT IN (164, 419, 173, 384, 461, 17)
    ORDER BY message.date DESC
''')

incoming_message_lengths = []
outgoing_message_lengths = []
message_counts_per_day = {}

for row in messages_db.fetchall():
    contact_id = row['id']
    text = row['text']

    arrow = "<-" if row['is_from_me'] else "->"

    if contact_id in contact_phone_canonical_index:
        myprint("HIT %s in contact_phone_canonical_index" % contact_id)
    elif contact_id in contact_email_index:
        myprint("HIT %s in contact_email_index" % contact_id)
    else:
        myprint("MISS %s in either index" % contact_id)
        if text != None:
            myprint("\t text was %s" % text.encode('utf8'))

    if row['is_from_me']:
        length = 0
        if (text != None):
            length = len(text)

        outgoing_message_lengths.append(length)
    else:
        length = 0
        if (text != None):
            length = len(text)

        incoming_message_lengths.append(length)

    datetime_string = datetime.strptime(row['time'], "%Y-%m-%d %H:%M:%S")
    datestring = datetime_string.strftime("%Y-%m-%d")
    if datestring in message_counts_per_day:
        message_counts_per_day[datestring] = message_counts_per_day[datestring] + 1
    else:
        message_counts_per_day[datestring] = 1

# Aspect ratio
plot.figure(figsize=(12, 9))  

# Remove the plot frame lines. They are unnecessary chartjunk.  
ax = plot.subplot(111)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)

# Ensure that the axis ticks only show up on the bottom and left of the plot.  
# Ticks on the right and top of the plot are generally unnecessary chartjunk.  
ax.get_xaxis().tick_bottom()  
ax.get_yaxis().tick_left()

# Make sure your axis ticks are large enough to be easily read.  
# You don't want your viewers squinting to read your plot.  
plot.xticks(fontsize=14)  
plot.yticks(range(5000, 30001, 5000), fontsize=14)

  
# Along the same vein, make sure your axis labels are large  
# enough to be easily read as well. Make them slightly larger  
# than your axis tick labels so they stand out.  
plot.xlabel("Character count per message", fontsize=16)  
plot.ylabel("Frequency", fontsize=16) 

plot.hist(x=outgoing_message_lengths, bins=200, alpha=0.5, range=(0, 400), linewidth=1, color='blue')
plot.hist(x=incoming_message_lengths, bins=200, alpha=0.5, range=(0, 400), linewidth=1, color='#CC0000')

# Always include your data source(s) and copyright notice!
plot.text(1300, -5000, "SMS Messages", fontsize=10)

# Finally, save the figure as a PNG.  
# You can also save it as a PDF, JPEG, etc.  
# Just change the file extension in this call.  
# bbox_inches="tight" removes all the extra whitespace on the edges of your plot.  
plot.savefig("character-count-incoming-outgoing-sms.png", bbox_inches="tight");

print(message_counts_per_day)
plot.figure(2)

plot.show()
