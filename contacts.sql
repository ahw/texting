.mode line

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

.exit
