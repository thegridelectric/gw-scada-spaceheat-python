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
    <xsl:include href="ScadaCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
    <FileSet>
        <FileSetFiles>
            <xsl:for-each select="$airtable//Schemas/Schema[(normalize-space(Alias) !='') and (Status = 'Active') and (ProtocolType = 'Json') ]">
                <xsl:variable name="local-alias" select="AliasRoot" />  
                <xsl:variable name="schema-id" select="SchemaId" />
                <xsl:variable name="class-name">
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="$local-alias" />
                    </xsl:call-template>
                </xsl:variable>
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/schema/gt/</xsl:text><xsl:value-of select="translate($local-alias,'.','_')"/><xsl:text>/</xsl:text>
                                <xsl:value-of select="translate($local-alias,'.','_')"/><xsl:text>_base.py</xsl:text></xsl:element>
                        

                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents">

   
<xsl:text>"""Base for </xsl:text><xsl:value-of select="Alias"/><xsl:text>"""
import json
from typing import List, NamedTuple</xsl:text> 
<xsl:if test="count($airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not (IsRequired = 'true')]) > 0">
<xsl:text>, Optional</xsl:text>
</xsl:if>
<xsl:if test="count($airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and ((normalize-space(SubTypeDataClass) != '') or (normalize-space(PrimitiveFormat) != ''))]) > 0">
<xsl:text>
import schema.property_format as property_format</xsl:text>
</xsl:if>

<xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)]">
<xsl:if test="IsEnum = 'true'">
<xsl:text>
from schema.enums.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(EnumLocalName,'.','_')"  />
</xsl:call-template>
<xsl:text>.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(EnumLocalName,'.','_')"  />
</xsl:call-template>
<xsl:text>_map import (
    </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
</xsl:call-template>
<xsl:text>,
    </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
</xsl:call-template>
<xsl:text>Map,
)</xsl:text>
</xsl:if>

<xsl:if test="(IsType = 'true') and ((IsList = 'true') or (normalize-space(SubTypeDataClass)=''))">
<xsl:text>
from schema.gt.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(SubMessageFormatAlias,'.','_')"  />
</xsl:call-template>
<xsl:text>.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(SubMessageFormatAlias,'.','_')"  />
</xsl:call-template>
<xsl:text>_maker import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
</xsl:if>
</xsl:for-each>
<xsl:text>


class </xsl:text>
<xsl:value-of select="$class-name"/><xsl:text>Base(NamedTuple):
    </xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)]">


    <xsl:if test="(IsPrimitive = 'true') and (IsRequired = 'true') and not (IsList = 'true')">
        <xsl:value-of select="Value"/><xsl:text>: </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template>
<xsl:text>  #
    </xsl:text>
    </xsl:if>


    <xsl:if test="(IsPrimitive = 'true') and (IsList = 'true')">
        <xsl:value-of select="Value"/><xsl:text>: List[</xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template>
<xsl:text>]
    </xsl:text>
    </xsl:if>


    <xsl:if test = "(IsEnum = 'true') and not(IsList = 'true')">
        <xsl:value-of select="Value"/><xsl:text>: </xsl:text>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
<xsl:text>  #
    </xsl:text>
    </xsl:if>


    <xsl:if test = "(IsEnum = 'true') and (IsList = 'true')">
        <xsl:value-of select="Value"/><xsl:text>: List[</xsl:text>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
<xsl:text>]
    </xsl:text>
    </xsl:if>


    <xsl:if test="(IsRequired = 'true') and (IsType = 'true') and not(normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
    <xsl:value-of select="Value"/><xsl:text>Id: str
    </xsl:text>
    </xsl:if>

    <xsl:if test="(IsType = 'true') and  (normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
        <xsl:value-of select="Value"/><xsl:text>: </xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
        </xsl:call-template>
        <xsl:text>  #
    </xsl:text>
        </xsl:if>

    <xsl:if test="(IsType = 'true') and (IsList = 'true')">
        <xsl:value-of select="Value"/><xsl:text>: List[</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
        </xsl:call-template>
        <xsl:text>]
    </xsl:text>
     </xsl:if>
    
</xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)  and not (IsRequired = 'true')]">
    <xsl:if test="(IsPrimitive = 'true')">
        <xsl:value-of select="Value"/><xsl:text>: Optional[</xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template>
<xsl:text>] = None
    </xsl:text>
    </xsl:if>   

    <xsl:if test="not(normalize-space(SubTypeDataClass) = '')">
        <xsl:value-of select="Value"/><xsl:text>Id: Optional[str] = None
    </xsl:text> 
    </xsl:if>
    </xsl:for-each>
    <xsl:text>TypeAlias: str = "</xsl:text><xsl:value-of select="Alias"/><xsl:text>"

    def as_type(self):
        return json.dumps(self.asdict())

    def asdict(self):
        d = self._asdict()</xsl:text>

      <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)]">
      <xsl:if test="not (IsRequired = 'true') and (normalize-space(SubTypeDataClass) = '')">
        <xsl:text>
        if d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] is None:
            del d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]</xsl:text>
      </xsl:if>
      <xsl:if test="not (IsRequired = 'true') and not (normalize-space(SubTypeDataClass) = '')">
        <xsl:text>
        if d["</xsl:text><xsl:value-of select="Value"/><xsl:text>Id"] is None:
            del d["</xsl:text><xsl:value-of select="Value"/><xsl:text>Id"]</xsl:text>
      </xsl:if>

    <xsl:if test="(IsEnum = 'true')">

        <xsl:variable name="local-enum-name">
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
            </xsl:call-template>
        </xsl:variable>
        <xsl:if test="not (IsList = 'true')">
      <xsl:text>
        del d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]
        d["</xsl:text>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="Value" />
        </xsl:call-template>
        <xsl:text>GtEnumSymbol"] = </xsl:text><xsl:value-of select="$local-enum-name"/>
        <xsl:text>Map.local_to_gt(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>)</xsl:text>
        </xsl:if>


        <xsl:if test="(IsList = 'true')">
        <xsl:text>
        del d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]
        </xsl:text>  
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
          </xsl:call-template> <xsl:text> = []
        for elt in self.</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>:
            </xsl:text>
            <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
          </xsl:call-template><xsl:text>.append(</xsl:text>
          <xsl:value-of select="$local-enum-name"/><xsl:text>Map.local_to_gt(elt))
        d["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
            <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
          </xsl:call-template> 
        </xsl:if>

    </xsl:if>


    <xsl:if test="(IsType = 'true') and  (normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
        <xsl:text>
        d["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"] = self.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>.asdict()</xsl:text>
        </xsl:if>

    <xsl:if test="(IsType = 'true') and (IsList = 'true')">
        <xsl:text>

        # Recursively call asdict() for the SubTypes
        </xsl:text>
        <xsl:call-template name="python-case">
           <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template> 
        <xsl:text> = []
        for elt in self.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>:
            </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template> 
        <xsl:text>.append(elt.asdict())
        d["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template> 
    </xsl:if>

    </xsl:for-each>
    <xsl:text>
        return d

    def derived_errors(self) -> List[str]:
        errors = []</xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)]">


    <xsl:if test="(IsPrimitive='true') and (IsRequired = 'true') and not (IsList='true')">
        <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template><xsl:text>):
            errors.append(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
                <xsl:value-of select="Value"/><xsl:text>} must have type </xsl:text>
                <xsl:call-template name="python-type">
                    <xsl:with-param name="gw-type" select="PrimitiveType"/>
                </xsl:call-template><xsl:text>."
            )</xsl:text>
            <xsl:if test="normalize-space(PrimitiveFormat) != ''">
            <xsl:text>
        if not property_format.is_</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="translate(PrimitiveFormat,'.','_')"  />
          </xsl:call-template>
        <xsl:text>(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>):
            errors.append(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
                <xsl:value-of select="Value"/><xsl:text>}"
                " must have format </xsl:text><xsl:value-of select="PrimitiveFormat"/><xsl:text>"
            )</xsl:text>
            </xsl:if>
    </xsl:if>


    <xsl:if test="(IsPrimitive='true') and (IsRequired = 'true') and (IsList='true')">
    <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, list):
            errors.append(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>} must have type list."
            )
        else:
            for elt in self.</xsl:text><xsl:value-of select="Value"/><xsl:text>:
                if not isinstance(elt, </xsl:text>
                <xsl:call-template name="python-type">
                    <xsl:with-param name="gw-type" select="PrimitiveType"/>
                </xsl:call-template>
        <xsl:text>):
                    errors.append(
                        f"elt {elt} of </xsl:text><xsl:value-of select="Value"/>
            <xsl:text> must have type </xsl:text>
                <xsl:call-template name="python-type">
                    <xsl:with-param name="gw-type" select="PrimitiveType"/>
                </xsl:call-template>
                <xsl:text>."
                    )</xsl:text>
            <xsl:if test="normalize-space(PrimitiveFormat) != ''">
                <xsl:text>
                if not property_format.is_</xsl:text>
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="translate(PrimitiveFormat,'.','_')"  />
                  </xsl:call-template>
                <xsl:text>(elt):
                    errors.append(
                        f"elt {elt} of </xsl:text><xsl:value-of select="Value"/>
                        <xsl:text> must have format </xsl:text><xsl:value-of select="PrimitiveFormat"/><xsl:text>"
                    )</xsl:text>
            </xsl:if>
    </xsl:if>


    <xsl:if test="(IsPrimitive='true') and not(IsRequired = 'true') and not (IsList='true')">
        <xsl:text>
        if self.</xsl:text><xsl:value-of select="Value"/><xsl:text>:
            if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, </xsl:text>
            <xsl:call-template name="python-type">
                <xsl:with-param name="gw-type" select="PrimitiveType"/>
            </xsl:call-template><xsl:text>):
                errors.append(
                    f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
                    <xsl:value-of select="Value"/><xsl:text>} must have type </xsl:text>
                    <xsl:call-template name="python-type">
                        <xsl:with-param name="gw-type" select="PrimitiveType"/>
                    </xsl:call-template><xsl:text>."
                )</xsl:text>
                <xsl:if test="normalize-space(PrimitiveFormat) != ''">
                <xsl:text>
            if not property_format.is_</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="translate(PrimitiveFormat,'.','_')"  />
                </xsl:call-template>
            <xsl:text>(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>):
                errors.append(
                    f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
                    <xsl:value-of select="Value"/><xsl:text>}"
                    " must have format </xsl:text><xsl:value-of select="PrimitiveFormat"/><xsl:text>"
                )</xsl:text>
                </xsl:if>
    </xsl:if>


    <xsl:if test="(IsEnum='true') and not (IsList = 'true')">
        <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, </xsl:text>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
        <xsl:text>):
            errors.append(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>} must have type {</xsl:text>
                <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
                <xsl:text>}."
            )</xsl:text>
    </xsl:if>   
    
    
    <xsl:if test="(IsEnum='true') and (IsList='true')">

        <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, list):
            errors.append(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>} must have type list."
            )
        else:
            for elt in self.</xsl:text><xsl:value-of select="Value"/><xsl:text>:
                if not isinstance(elt, </xsl:text>
                <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
    </xsl:call-template>
        <xsl:text>):
                    errors.append(
                        f"elt {elt} of </xsl:text><xsl:value-of select="Value"/>
            <xsl:text> must have type </xsl:text>
                <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
                <xsl:text>."
                    )</xsl:text>
    </xsl:if>


     <xsl:if test="(IsRequired = 'true') and (normalize-space(SubTypeDataClass) != '') and not(IsList = 'true')">
        <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>Id, str):
            errors.append(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text>Id {self.</xsl:text>
            <xsl:value-of select="Value"/><xsl:text>Id} must have type str."
            )
        if not property_format.is_uuid_canonical_textual(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>Id):
            errors.append(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text>Id {self.</xsl:text>
                <xsl:value-of select="Value"/><xsl:text>Id}"
                " must have format UuidCanonicalTextual"
            )</xsl:text>
    </xsl:if>

    <xsl:if test="not (IsRequired = 'true') and (normalize-space(SubTypeDataClass) != '') and not(IsList = 'true')">
        <xsl:text>
        if self.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>Id:
            if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>Id, str):
                errors.append(
                    f"</xsl:text><xsl:value-of select="Value"/><xsl:text>Id {self.</xsl:text>
                <xsl:value-of select="Value"/><xsl:text>Id} must have type str."
                )
            if not property_format.is_uuid_canonical_textual(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>Id):
                errors.append(
                    f"</xsl:text><xsl:value-of select="Value"/><xsl:text>Id {self.</xsl:text>
                    <xsl:value-of select="Value"/><xsl:text>Id}"
                    " must have format UuidCanonicalTextual"
                )</xsl:text>
    </xsl:if>

    <xsl:if test="(IsType='true') and (normalize-space(SubTypeDataClass) = '') and not(IsList = 'true')">
        <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, </xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
        </xsl:call-template>
        <xsl:text>):
            errors.append(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text>
            <xsl:value-of select="Value"/><xsl:text>} must have type</xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
            </xsl:call-template>
            <xsl:text>."
            )</xsl:text>
    </xsl:if>


    <xsl:if test="(IsType = 'true') and (IsList = 'true')">
        <xsl:text>
        if not isinstance(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>, list):
            errors.append(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text> {self.</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>} must have type list."
            )
        else:
            for elt in self.</xsl:text><xsl:value-of select="Value"/><xsl:text>:
                if not isinstance(elt, </xsl:text>
                <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
    </xsl:call-template>
        <xsl:text>):
                    errors.append(
                        f"elt {elt} of </xsl:text><xsl:value-of select="Value"/>
            <xsl:text> must have type </xsl:text>
                <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
        </xsl:call-template>
                <xsl:text>."
                    )</xsl:text>
    </xsl:if>
        </xsl:for-each>
        <xsl:text>
        if self.TypeAlias != "</xsl:text><xsl:value-of select="Alias"/><xsl:text>":
            errors.append(
                f"Type requires TypeAlias of </xsl:text><xsl:value-of select="Alias"/><xsl:text>, not {self.TypeAlias}."
            )

        return errors
</xsl:text>

                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>