<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:msxsl="urn:schemas-microsoft-com:xslt" exclude-result-prefixes="msxsl" xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xsl:output method="xml" indent="yes" />
    <xsl:param name="root" />
    <xsl:param name="codee-root" />
    <xsl:include href="../CommonXsltTemplates.xslt"/>
    <xsl:param name="exclude-collections" select="'false'" />
    <xsl:param name="relationship-suffix" select="''" />
    <xsl:variable name="airtable" select="/" />
    <xsl:variable name="squot">'</xsl:variable>
    <xsl:variable name="init-space">             </xsl:variable>
    <xsl:include href="GwSchemaCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
        <FileSet>
            <FileSetFiles>
                <xsl:for-each select="$airtable//MpSchemas/MpSchema[(normalize-space(Alias) !='')  and (FromDataClass='true') and ((Alias = 'gt.component.1_1_0')  or (Alias = 'gt.component.attribute.class.1_1_0')) and ((Status = 'Active') or (Status = 'Supported') or (Status = 'Pending'))]">
                    <xsl:variable name="mp-schema-alias" select="Alias" />  
                    <xsl:variable name="mp-schema-id" select="MpSchemaId" />
                    <xsl:variable name="class-name">
                        <xsl:call-template name="message-case">
                            <xsl:with-param name="mp-schema-text" select="Alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="nt-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="mp-schema-text" select="Alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="routing-key-base">
                        <xsl:if test="MessagePassingMechanism = 'SassyRabbit.3_0'">
                            <xsl:value-of select="translate(SassyFrom, $ucletters, $lcletters)"/><xsl:text>.</xsl:text>
                            <xsl:value-of select="translate(SassyMessage, $ucletters, $lcletters)"/><xsl:text>.</xsl:text>
                           <xsl:value-of select="translate(SassyTo, $ucletters, $lcletters)"/>
                       </xsl:if>
                        <xsl:if test="MessagePassingMechanism = 'SassyRabbit.2_0'">
                            <xsl:value-of select="translate(SassyTo, $ucletters, $lcletters)"/><xsl:text>.custom.</xsl:text>
                            <xsl:value-of select="translate(SassyFrom, $ucletters, $lcletters)"/><xsl:text>.</xsl:text>
                            <xsl:value-of select="translate(SassyMessage, $ucletters, $lcletters)"/>
                        </xsl:if>
                        <xsl:if test="MessagePassingMechanism = 'SassyRabbit.1_0'">
                            <xsl:value-of select="translate(SassyTo, $ucletters, $lcletters)"/><xsl:text>.general.</xsl:text>
                            <xsl:value-of select="translate(SassyFrom, $ucletters, $lcletters)"/><xsl:text>.</xsl:text>
                            <xsl:value-of select="translate(SassyMessage, $ucletters, $lcletters)"/>
                        </xsl:if>
                    </xsl:variable>
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/schema/gt/gnr/</xsl:text><xsl:value-of select="NtClass"/><xsl:text>/</xsl:text>
                                <xsl:value-of select="translate(Alias,'.','_')"/><xsl:text>_schema_base.py</xsl:text></xsl:element>
                        

                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents">

   
<xsl:text>"""SchemaBase for </xsl:text><xsl:value-of select="$mp-schema-alias"/><xsl:text>"""
from typing import List, Tuple, Optional, NamedTuple
import schema.property_format</xsl:text>

<xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and TypeIsNtClass='true']">
<xsl:if test="FromDataClass='true'">
<xsl:text>
from schema.gt.gnr.</xsl:text><xsl:value-of select="NtClass"/><xsl:text>.</xsl:text>
<xsl:value-of select="translate(SubMessageFormatAlias,'.','_')"/><xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
</xsl:if>
<xsl:if test="not(FromDataClass='true')">
<xsl:text>
from schema.gt.</xsl:text><xsl:value-of select="NtClass"/><xsl:text>.</xsl:text>
<xsl:value-of select="translate(SubMessageFormatAlias,'.','_')"/><xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
</xsl:if>
    </xsl:for-each>

<xsl:text>


class SchemaBase(NamedTuple):
    </xsl:text>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true' and (IsRequired = 'true')]">
        <xsl:value-of select="Value"/><xsl:text>: </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
        </xsl:call-template><xsl:text>     #
    </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired = 'true') and not (normalize-space(TypeInPayload) = 'List') and (TypeIsNtClass = 'true')]">
    <xsl:value-of select="Value"/><xsl:text>: </xsl:text>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
    </xsl:call-template><xsl:text>     #
    </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired = 'true') and not (normalize-space(TypeInPayload) = 'List') and not (TypeIsNtClass = 'true')]">
        <xsl:value-of select="Value"/><xsl:text>: </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
        </xsl:call-template><xsl:text>     #
    </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired = 'true') and (normalize-space(TypeInPayload) = 'List') and (TypeIsNtClass = 'true') ]">
        <xsl:value-of select="Value"/><xsl:text>: List[</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
        </xsl:call-template><xsl:text>]
    </xsl:text>
    </xsl:for-each>
    <xsl:if test="not (IsNamedTuple = 'true') and (AlwaysSimulated = 'true')">
    <xsl:text>WorldInstanceAlias: str
    </xsl:text>
        </xsl:if>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired = 'true') and (normalize-space(TypeInPayload) = 'List') and not (TypeIsNtClass = 'true') ]">
    <xsl:value-of select="Value"/><xsl:text>: List[</xsl:text>
    <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template><xsl:text>]
    </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired = 'true') and not (normalize-space(TypeInPayload) = 'List') and (TypeIsNtClass = 'true')]">
    <xsl:value-of select="Value"/><xsl:text>: Optional[</xsl:text>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
    </xsl:call-template><xsl:text>] = None
    </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired = 'true') and not (normalize-space(TypeInPayload) = 'List') and not (TypeIsNtClass = 'true')]">
        <xsl:value-of select="Value"/><xsl:text>: Optional[</xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
        </xsl:call-template><xsl:text>] = None
    </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired = 'true') and (normalize-space(TypeInPayload) = 'List') and (TypeIsNtClass = 'true') ]">
        <xsl:value-of select="Value"/><xsl:text>: Optional[List[</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
        </xsl:call-template><xsl:text>]] = None
    </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired = 'true') and (normalize-space(TypeInPayload) = 'List') and not (TypeIsNtClass = 'true') ]">
    <xsl:value-of select="Value"/><xsl:text>: Optional[List[</xsl:text>
    <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template><xsl:text>]] = None
    </xsl:text>
    </xsl:for-each>
    <xsl:if test="not (IsNamedTuple = 'true') and not(AlwaysSimulated = 'true')">
    <xsl:text>WorldInstanceAlias: Optional[str] = None
    </xsl:text>
    </xsl:if>

    <xsl:text>MpAlias: str = '</xsl:text><xsl:value-of select="$mp-schema-alias"/><xsl:text>'

    def asdict(self):
        d = self._asdict()</xsl:text>
<xsl:if test="not (IsNamedTuple = 'true') and not(AlwaysSimulated = 'true')">
<xsl:text>
        if d["WorldInstanceAlias"] is None:
            del d["WorldInstanceAlias"]</xsl:text>
</xsl:if>
      <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and not (IsRequired = 'true')]">
        <xsl:text>
        if d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] is None:
            del d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]</xsl:text>
      </xsl:for-each>
      <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and (IsRequired = 'true') and (TypeIsNtClass='true') and not (IsList='true')]">
      <xsl:text>
        d['</xsl:text><xsl:value-of select="Value"/><xsl:text>'] = d['</xsl:text><xsl:value-of select="Value"/><xsl:text>'].asdict()</xsl:text>    
      </xsl:for-each>
      <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and (IsRequired = 'true') and (TypeIsNtClass='true') and (IsList='true')]">
      <xsl:text>
        list_of_dicts = []
        for elt in d['</xsl:text><xsl:value-of select="Value"/><xsl:text>']:
            list_of_dicts.append(elt.asdict())
        d['</xsl:text><xsl:value-of select="Value"/><xsl:text>'] = list_of_dicts</xsl:text>  
      </xsl:for-each>
<xsl:text>
        return d

    def passes_derived_validations(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid = True
        errors = []
        if self.MpAlias != '</xsl:text><xsl:value-of select="Alias"/><xsl:text>':
            is_valid = False
            errors.append(f"Payload requires MpAlias of </xsl:text><xsl:value-of select="Alias"/><xsl:text>, not {self.MpAlias}.")</xsl:text>
<xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true' and normalize-space(IsRequired) = 'true']">
    <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, </xsl:text>
            <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
          </xsl:call-template>
    <xsl:text>):
            is_valid = False
            errors.append(f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
    <xsl:value-of select="Value"/><xsl:text>} must have type </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
        </xsl:call-template><xsl:text>.")</xsl:text>
    <xsl:if test="normalize-space(FormatAlias) !=''">
        <xsl:text>
        if not schema.property_format.is_</xsl:text>
          <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="translate(FormatAlias,'.','_')"  />
          </xsl:call-template>
         <xsl:text>(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>):
            is_valid = False
            errors.append(f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
            <xsl:value-of select="Value"/><xsl:text>} must have format </xsl:text>
            <xsl:value-of select="translate(FormatAlias,'.','_')"/>
    <xsl:text>.")</xsl:text>
   </xsl:if>
</xsl:for-each>
<xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true' and not (normalize-space(IsRequired) = 'true')]">
    <xsl:text>
        if self.</xsl:text><xsl:value-of select="Value"/><xsl:text>:
            if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, </xsl:text>
                <xsl:call-template name="python-type">
                <xsl:with-param name="gw-type" select="TypeInPayload"/>
              </xsl:call-template>
        <xsl:text>):
                is_valid = False
                errors.append(f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>} must have type </xsl:text>
            <xsl:call-template name="python-type">
                <xsl:with-param name="gw-type" select="TypeInPayload"/>
            </xsl:call-template><xsl:text>.")</xsl:text>
        <xsl:if test="normalize-space(FormatAlias) !=''">
            <xsl:text>
            if not schema.property_format.is_</xsl:text>
              <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="translate(FormatAlias,'.','_')"  />
              </xsl:call-template>
             <xsl:text>(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>):
                is_valid = False
                errors.append(f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
                <xsl:value-of select="Value"/><xsl:text>} must have format </xsl:text>
                <xsl:value-of select="translate(FormatAlias,'.','_')"/>
        <xsl:text>.")</xsl:text>
   </xsl:if>
</xsl:for-each>
<xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (normalize-space(IsRequired) = 'true')]">
<xsl:if test="not (TypeInPayload = 'List') and (TypeIsNtClass = 'true')">
    <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, </xsl:text>
  <xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
    </xsl:call-template>
  <xsl:text>):
            is_valid = False
            raise Exception(f"Make sure </xsl:text><xsl:value-of select="Value"/><xsl:text> has type </xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                </xsl:call-template>
            <xsl:text>")
        new_is_valid, new_errors = self.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>.is_valid()
        if not new_is_valid:
            is_valid = False
            errors += new_errors</xsl:text>

</xsl:if>
<xsl:if test="(TypeInPayload = 'List') or not (TypeIsNtClass = 'true')">
    <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
        </xsl:call-template><xsl:text>):
            is_valid = False
            errors.append(f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
            <xsl:value-of select="Value"/><xsl:text>} must have type </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
        </xsl:call-template>
        <xsl:text>.")</xsl:text>
   <xsl:if test="normalize-space(FormatAlias) !=''">
        <xsl:text>
        if not schema.property_format.is_</xsl:text>
          <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="translate(FormatAlias,'.','_')"  />
          </xsl:call-template>
         <xsl:text>(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>):
            is_valid = False
            errors.append(f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
            <xsl:value-of select="Value"/><xsl:text>} must have format </xsl:text>
            <xsl:value-of select="translate(FormatAlias,'.','_')"/>
    <xsl:text>.")</xsl:text>
   </xsl:if>
</xsl:if>
   <xsl:if test="(IsList ='true') and (TypeIsNtClass = 'true')">
       <xsl:text>
        else:
            for elt in self.</xsl:text><xsl:value-of select="Value"/> <xsl:text>:
                if not isinstance(elt, </xsl:text> 
                <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                </xsl:call-template>
                <xsl:text>):
                    raise Exception(f"Elements of the list </xsl:text> <xsl:value-of select="Value"/>
                    <xsl:text> must have type </xsl:text>
                    <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                    </xsl:call-template><xsl:text>. Error with {elt}")
                new_is_valid, new_errors = elt.is_valid()
                if not new_is_valid:
                    is_valid = False
                    errors += new_errors</xsl:text>

   </xsl:if>
   <xsl:if test="(IsList ='true') and not (TypeIsNtClass = 'true')">
       <xsl:text>
        else:
            for elt in self.</xsl:text><xsl:value-of select="Value"/> <xsl:text>:
                if not isinstance(elt, </xsl:text> 
                <xsl:call-template name="python-type">
                    <xsl:with-param name="gw-type" select="PrimitiveType"/>
                </xsl:call-template><xsl:text>):    
                    is_valid = False
                    errors.append(f"Elements of the list </xsl:text> <xsl:value-of select="Value"/>
                    <xsl:text> must have type </xsl:text>
                    <xsl:call-template name="python-type">
                        <xsl:with-param name="gw-type" select="PrimitiveType"/>
                    </xsl:call-template><xsl:text>. Error with {elt}")</xsl:text>
   </xsl:if>
</xsl:for-each>
<xsl:if test="not (IsNamedTuple='true') and not (AlwaysSimulated = 'true')">
<xsl:text>
        if self.WorldInstanceAlias:
            if not isinstance(self.WorldInstanceAlias, str):
                is_valid = False
                errors.append(f"WorldInstanceAlias {self.WorldInstanceAlias} must have type str.")
            if not schema.property_format.is_world_instance_alias_format(self.WorldInstanceAlias):
                is_valid = False
                errors.append(f"WorldInstanceAlias {self.WorldInstanceAlias} must have format WorldInstanceAliasFormat")</xsl:text>

</xsl:if>
<xsl:if test="not (IsNamedTuple='true') and(AlwaysSimulated = 'true')">
<xsl:text>
        if not isinstance(self.WorldInstanceAlias, str):
            is_valid = False
            errors.append(f"WorldInstanceAlias {self.WorldInstanceAlias} must have type str.")
        if not schema.property_format.is_world_instance_alias_format(self.WorldInstanceAlias):
            is_valid = False
            errors.append(f"WorldInstanceAlias {self.WorldInstanceAlias} must have format WorldInstanceAliasFormat")</xsl:text>

</xsl:if>
<xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (normalize-space(IsRequired) = 'true')]">
<xsl:text>
        if self.</xsl:text><xsl:value-of select="Value"/><xsl:text>:
            if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, </xsl:text>
            <xsl:if test="TypeIsNtClass = 'true'">
                <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                </xsl:call-template>
            </xsl:if>
            <xsl:if test="not (TypeIsNtClass = 'true')">
            <xsl:call-template name="python-type">
                <xsl:with-param name="gw-type" select="TypeInPayload"/>
            </xsl:call-template>
            </xsl:if>
            <xsl:text>):
                is_valid = False
                errors.append(f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
                <xsl:value-of select="Value"/><xsl:text>} must have type </xsl:text>
                <xsl:if test="TypeIsNtClass = 'true'">
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                    </xsl:call-template>
                </xsl:if>
            <xsl:if test="not (TypeIsNtClass = 'true')">
            <xsl:call-template name="python-type">
                <xsl:with-param name="gw-type" select="TypeInPayload"/>
            </xsl:call-template>
            </xsl:if>
            <xsl:text>.")</xsl:text>
       <xsl:if test="normalize-space(FormatAlias) !=''">
            <xsl:text>
            if not schema.property_format.is_</xsl:text>
              <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="translate(FormatAlias,'.','_')"  />
              </xsl:call-template>
             <xsl:text>(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>):
                is_valid = False
                errors.append(f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
                <xsl:value-of select="Value"/><xsl:text>} must have format </xsl:text>
                <xsl:value-of select="translate(FormatAlias,'.','_')"/>
        <xsl:text>.")</xsl:text>
   </xsl:if>
</xsl:for-each>
<xsl:text>
        return is_valid, errors

</xsl:text>

                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>