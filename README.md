SQLite3 Files
-------------
| Content    | Real Name            | Backup filename                          |
| ---        | ---                  | ---                                      |
| SMS        | sms.db               | 3d0d7e5fb2ce288813306e4d4636395e047a3d28 |
| Contacts   | AddressBook.sqlitedb | 31bb7ba8914766d4ba40d6dfb6113c8b614be442 |
| Calendar   | Calendar.sqlitedb    | 2041457d5fe04d39d0ab481178355df6781e6858 |
| Reminders  | Calendar.sqlitedb    | 2041457d5fe04d39d0ab481178355df6781e6858 |
| Notes      | notes.sqlite         | ca3bc056d4da0bbf88b5fb3be254f3b7147e639c |
| Call hist. | call_history.db      | 2b2b0084a1bc3a5ac8c27afdf14afb42c61a19ca |
| Locations  | consolidated.db      | 4096c9ec676f2847dc283405900e284a7c815836 |

Python setup
------------

    virtualenv env-ml
    source env-ml/bin/activate
    pip install numpy scikit-learn matplotlib

[matplotlib-not-showing-up-in-mac-osx](http://stackoverflow.com/questions/2512225/matplotlib-not-showing-up-in-mac-osx)
[matplotlibrc](http://matplotlib.sourceforge.net/_static/matplotlibrc)

    touch ~/.matplotlib/matplotlibrc
    # Not necessary. Realized I just had the plotting window hidden
    brew install qt
    pip install PySide

SQLite Schema
-------------

File located at either
- `~/Library/Application\ Support/MobileSync/Backup/02e365729661dbc3315d705c72c5a3524843eb32/3d0d7e5fb2ce288813306e4d4636395e047a3d28`
- `~/Library/Application\ Support/MobileSync/Backup/02e365729661dbc3315d705c72c5a3524843eb32/3d/3d0d7e5fb2ce288813306e4d4636395e047a3d28`

[iPhone SQLite3 SMS database schema](https://s3.amazonaws.com/pd93f014/schema.sql.html)

Internal Schemas
----------------

## contacts
Dictionary containing the "merged" values from `ABPerson` (first name, last
name, etc.) and `ABMultiValue` (email address, phone number). Apple stores
each contact "value" separately in in `ABMultiValue`, so the email address
and phone number for John Smith each have their own row in `ABMultiValue`.
They are connected by the `record_id`. I am iterating over `ABPerson JOIN
ABMultiValue` and merging these values so at the end, `contacts` looks
something like this:

```
<record_id>: {
    phone_row: "+1 (555) 123-4567"
    phone_digits_only: 15551234567
    phone_canonical: "+15551234567"
    phone_hash: "<SHA1 hash of phone_canonical>"
    email: "johnsmith@example.com"
    first: "John"
    last: "Smith"
    organization: "Starbucks"
}
```

## contact_phone_canonical_index
Maps `phone_canonical` to the appropriate `contacts[record_id]` entry.

```
phone_canonical       contacts
---------------      +-------------------------------
+15551234567 ------> | phone_row: "+1 (555) 123-4567"
                     | phone_digits_only: 15551234567
                     | phone_canonical: "+15551234567"
                     | phone_hash: "<SHA1 hash of phone_canonical>"
                     | email: "johnsmith@example.com"
                     | first: "John"
                     | last: "Smith"
                     | organization: "Starbucks"
                     +--------------------------

                     +-----
+15559876543 ------> | ...
                     | ...
                     |
                     +-----
```

## contact_email_index
Maps `email` (unparsed) to the appropriate `contacts[record_id]` entry.

```
email                          contacts
-----                         +-------------------------------
johnsmith@example.com ------> | phone_row: "+1 (555) 123-4567"
                              | phone_digits_only: 15551234567
                              | phone_canonical: "+15551234567"
                              | phone_hash: "<SHA1 hash of phone_canonical>"
                              | email: "johnsmith@example.com"
                              | first: "John"
                              | last: "Smith"
                              | organization: "Starbucks"
                              +--------------------------

                              +-----
someoneelse@someplace.com --> | ...
                              | ...
                              |
                              +-----
```
