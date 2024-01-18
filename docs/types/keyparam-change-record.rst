KeyparamChangeRecord
==========================
Python pydantic class corresponding to json type `keyparam.change.record`, version `000`.

.. autoclass:: gwstypes.KeyparamChangeRecord
    :members:

**AboutNodeAlias**:
    - Description: AboutNodeAlias. The GNode (for example, the SCADA or the AtomicTNode) whose parameter is getting changed.
    - Format: LeftRightDot

**ChangeTimeUtc**:
    - Description: Change Time Utc. The time of the change. Err on the side of making sure the original parameter was used by the code at all times prior to this time. Do not be off by more than 5 minutes.
    - Format: LogStyleDateWithMillis

**Author**:
    - Description: Author. The person making the change.

**ParamName**:
    - Description: ParamName. This may not be unique or even particularly well-defined on its own. But this can set the context for the recommended 'Before' and 'After' fields associated to this type.

**Description**:
    - Description: Description. Clear concise description of the change. Consider including why it is a key parameter.

**Kind**:
    - Description: Kind of Param. This should provide a developer with the information they need to locate the parameter and its use within the relevant code base.

**TypeName**:
    - Description: All GridWorks Versioned Types have a fixed TypeName, which is a string of lowercase alphanumeric words separated by periods, most significant word (on the left) starting with an alphabet character, and final word NOT all Hindu-Arabic numerals.

**Version**:
    - Description: All GridWorks Versioned Types have a fixed version, which is a string of three Hindu-Arabic numerals.



.. autoclass:: gwtypes.keyparam_change_record.check_is_left_right_dot
    :members:


.. autoclass:: gwtypes.keyparam_change_record.check_is_log_style_date_with_millis
    :members:


.. autoclass:: gwproto.types.KeyparamChangeRecord_Maker
    :members:

