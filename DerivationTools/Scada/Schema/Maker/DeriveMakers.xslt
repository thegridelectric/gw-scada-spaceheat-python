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
                <xsl:for-each select="$airtable//Schemas/Schema[(normalize-space(Alias) !='') and (Status = 'Active') and (ProtocolType = 'Json')]">
                <xsl:variable name="local-alias" select="AliasRoot" />
                <xsl:variable name="schema-id" select="SchemaId" />  
                <xsl:variable name="class-name">
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="$local-alias" />
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="python-data-class">
                    <xsl:call-template name="python-case">
                        <xsl:with-param name="camel-case-text" select="translate(DataClass,'.','_')"  />
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="data-class-id">
                    <xsl:if test="IsCac='true'">
                        <xsl:text>component_attribute_class_id</xsl:text>
                    </xsl:if>
                    <xsl:if test="IsComponent='true'">
                        <xsl:text>component_id</xsl:text>
                    </xsl:if>
                    
                    <xsl:if test="not (IsCac='true') and not (IsComponent='true')">
                        <xsl:value-of select="$python-data-class"/><xsl:text>_id</xsl:text>
                   </xsl:if>
                </xsl:variable>
                <FileSetFile>
                            <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/schema/gt/</xsl:text>
                            <xsl:value-of select="translate($local-alias,'.','_')"/><xsl:text>/</xsl:text>
                            <xsl:value-of select="translate($local-alias,'.','_')"/><xsl:text>_maker.py</xsl:text></xsl:element>

                    <OverwriteMode>Always</OverwriteMode>
                    <xsl:element name="FileContents">

<xsl:text>"""Makes </xsl:text><xsl:value-of select="Alias"/><xsl:text> type"""
import json</xsl:text>
<xsl:if test="count($airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not(IsRequired = 'true')])>0">
<xsl:if test="count($airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsList = 'true')])=0">
<xsl:text>
from typing import Optional</xsl:text>
</xsl:if>
<xsl:if test="count($airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsList = 'true')])>0">
<xsl:text>
from typing import List, Optional</xsl:text>
</xsl:if>
</xsl:if>

<xsl:if test="count($airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsList = 'true')])>0">
<xsl:if test="count($airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not(IsRequired = 'true')])=0">
<xsl:text>
from typing import List</xsl:text>
</xsl:if>
</xsl:if>
<xsl:if test="MakeDataClass='true'">
<xsl:if test="IsCac = 'true'">
<xsl:text>
from data_classes.cacs.</xsl:text>
<xsl:value-of select="$python-data-class"/>
<xsl:text> import </xsl:text><xsl:value-of select="DataClass"/>
</xsl:if>
<xsl:if test="IsComponent = 'true'">
<xsl:text>
from data_classes.components.</xsl:text>
<xsl:value-of select="$python-data-class"/>
<xsl:text> import </xsl:text><xsl:value-of select="DataClass"/>
</xsl:if>
<xsl:if test="not(IsComponent = 'true') and not(IsCac = 'true')">
<xsl:text>
from data_classes.</xsl:text>
<xsl:value-of select="$python-data-class"/>
<xsl:text> import </xsl:text><xsl:value-of select="DataClass"/>
</xsl:if>
</xsl:if>
<xsl:text>

from schema.gt.</xsl:text> <xsl:value-of select="translate($local-alias,'.','_')"/>
<xsl:text>.</xsl:text><xsl:value-of select="translate($local-alias,'.','_')"/>
<xsl:text> import </xsl:text><xsl:value-of select="$class-name"/><xsl:text>
from schema.errors import MpSchemaError</xsl:text>

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
<xsl:text>_maker import (
    </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
<xsl:text>,
    </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
<xsl:text>_Maker,
)</xsl:text>
</xsl:if>
</xsl:for-each>
<xsl:text>


class </xsl:text>
<xsl:value-of select="$class-name"/>
<xsl:text>_Maker:
    type_alias = "</xsl:text><xsl:value-of select="Alias"/><xsl:text>"

    def __init__(self</xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsRequired='true')]">
        <xsl:if test="(IsPrimitive = 'true') and not (IsList = 'true')">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>: </xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template>
        </xsl:if>

        <xsl:if test="(IsPrimitive = 'true') and (IsList = 'true')">
                <xsl:text>,
                 </xsl:text>
            <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>: List[</xsl:text>
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template><xsl:text>]</xsl:text>
        </xsl:if>


        <xsl:if test="IsEnum = 'true' and not (IsList = 'true')">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>: </xsl:text>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
        </xsl:if>

        <xsl:if test="IsEnum = 'true' and (IsList = 'true')">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>: List[</xsl:text>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template><xsl:text>]</xsl:text>
        </xsl:if>

        <xsl:if test="(IsType = 'true') and not(normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>_id: str</xsl:text>
        </xsl:if>

        <xsl:if test="(IsType = 'true') and  (normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
                <xsl:text>,
                 </xsl:text>
                    <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>: </xsl:text>
                <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                </xsl:call-template>
        </xsl:if>

        <xsl:if test="(IsType = 'true') and (IsList = 'true')">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>: List[</xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
            </xsl:call-template>
                <xsl:text>]</xsl:text>
        </xsl:if>
     </xsl:for-each>

     <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not (IsRequired='true')]">


        <xsl:if test=" (IsPrimitive = 'true') ">
                <xsl:text>,
                 </xsl:text>
                <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>: Optional[</xsl:text>
            <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
            </xsl:call-template><xsl:text>]</xsl:text>
        </xsl:if>

        <xsl:if test="not(normalize-space(SubTypeDataClass) = '')">
                <xsl:text>,
                 </xsl:text>
            <xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>_id: Optional[str]</xsl:text>
        </xsl:if>
        </xsl:for-each>
    <xsl:text>):

        gw_tuple = </xsl:text><xsl:value-of select="$class-name"/>
        <xsl:text>(
            </xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)]">
        <xsl:if test="(IsPrimitive = 'true') or (IsEnum = 'true')">
        <xsl:value-of select="Value"/><xsl:text>=</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>,
            </xsl:text>
        </xsl:if>

        <xsl:if test="(IsType = 'true') and not(normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
            <xsl:value-of select="Value"/><xsl:text>Id=</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
        <xsl:text>_id,
            </xsl:text>
        </xsl:if>

        <xsl:if test="(IsType = 'true') and ((normalize-space(SubTypeDataClass) = '') or (IsList = 'true'))">
            <xsl:value-of select="Value"/><xsl:text>=</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
        <xsl:text>,
            </xsl:text>
        </xsl:if>

    </xsl:for-each>
    <xsl:text>#
        )
        gw_tuple.check_for_errors()
        self.tuple = gw_tuple

    @classmethod
    def tuple_to_type(cls, tuple: </xsl:text><xsl:value-of select="$class-name"/>
    <xsl:text>) -> str:
        tuple.check_for_errors()
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: str) -> </xsl:text><xsl:value-of select="$class-name"/>
<xsl:text>:
        try:
            d = json.loads(t)
        except TypeError:
            raise MpSchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise MpSchemaError(f"Deserializing {t} must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict) -> </xsl:text><xsl:value-of select="$class-name"/>
<xsl:text>:
        new_d = {}
        for key in d.keys():
            new_d[key] = d[key]
        if "TypeAlias" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing TypeAlias")</xsl:text>
<xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)]">
<xsl:if test="(IsPrimitive = 'true') and (IsRequired = 'true')">
<xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing </xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>")</xsl:text>
</xsl:if>

<xsl:if test="(IsType = 'true') and (normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
<xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing </xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>")
        if not isinstance(new_d["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"], dict):
            raise MpSchemaError(f"d['</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>'] {new_d['</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>']} must be a </xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
            </xsl:call-template>
            <xsl:text>!")
        </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text> = </xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
        </xsl:call-template>
        <xsl:text>_Maker.dict_to_tuple(new_d["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"])
        new_d["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
</xsl:if>


<xsl:if test="(IsRequired = 'true') and not(normalize-space(SubTypeDataClass) = '') and not(IsList = 'true')">
<xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>Id" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing </xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>Id")</xsl:text>
</xsl:if>
<xsl:if test="not(IsRequired = 'true') and not(normalize-space(SubTypeDataClass) = '') and not(IsList = 'true')">
<xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>Id" not in new_d.keys():
            new_d["</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>Id"] = None</xsl:text>
</xsl:if>


<xsl:if test="(IsType = 'true') and (IsList = 'true')">
    <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing </xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>")
        </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text> = []
        for elt in new_d["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"]:
            if not isinstance(elt, dict):
                raise MpSchemaError(
                    f"elt {elt} of </xsl:text>
                    <xsl:value-of select="Value"/>
                    <xsl:text> must be "
                    "</xsl:text>
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                    </xsl:call-template>
                    <xsl:text> but not even a dict!"
                )
            </xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
            <xsl:text>.append(
                </xsl:text>
                <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                </xsl:call-template>
                <xsl:text>_Maker.dict_to_tuple(elt)
            )
        new_d["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>

</xsl:if>


<xsl:if test="(IsEnum = 'true') and  not (IsList = 'true')">
<xsl:text>
        if "</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="Value" />
        </xsl:call-template><xsl:text>GtEnumSymbol" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing </xsl:text>
            <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="Value" />
        </xsl:call-template>
            <xsl:text>GtEnumSymbol")
        new_d["</xsl:text> <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="Value" />
        </xsl:call-template><xsl:text>"] = </xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
        <xsl:text>Map.gt_to_local(new_d["</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="Value" />
        </xsl:call-template><xsl:text>GtEnumSymbol"])</xsl:text>
 </xsl:if>


<xsl:if test="(IsEnum = 'true') and (IsList = 'true')">
<xsl:text>
        if "</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>" not in new_d.keys():
            raise MpSchemaError(f"dict {new_d} missing </xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>")
        </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text> = []
        for elt in new_d["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"]:
            </xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
            <xsl:text>.append(</xsl:text>
            <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template>
            <xsl:text>Map.gt_to_local(elt))
        new_d["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
</xsl:if>

<xsl:if test="(IsPrimitive = 'true') and not(IsRequired = 'true')">
<xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" not in new_d.keys():
            new_d["</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>"] = None</xsl:text>
</xsl:if>
</xsl:for-each>
<xsl:text>

        gw_tuple = </xsl:text><xsl:value-of select="$class-name"/><xsl:text>(
            TypeAlias=new_d["TypeAlias"],
            </xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)]">
        <xsl:if test="(IsPrimitive = 'true') or (IsEnum = 'true') or (normalize-space(SubTypeDataClass) = '') or  (IsList = 'true')">
        <xsl:value-of select="Value"/><xsl:text>=new_d["</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>"],
            </xsl:text>
        </xsl:if>

        <xsl:if test="(IsType = 'true') and not(normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
        <xsl:value-of select="Value"/><xsl:text>Id=new_d["</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>Id"],
            </xsl:text>
        </xsl:if>
        </xsl:for-each>
        <xsl:text>#
        )
        gw_tuple.check_for_errors()
        return gw_tuple
</xsl:text>
    <xsl:if test="(MakeDataClass='true')">
    <xsl:text>
    @classmethod
    def tuple_to_dc(cls, t: </xsl:text><xsl:value-of select="$class-name"/>
    <xsl:text>) -> </xsl:text><xsl:value-of select="DataClass"/><xsl:text>:
        s = {
            </xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsPrimitive = 'true')]">
            <xsl:text>"</xsl:text>
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template><xsl:text>": t.</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>,
            </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsType = 'true')]">
            <xsl:text>"</xsl:text>
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template><xsl:text>_id": t.</xsl:text>
        <xsl:value-of select="Value"/><xsl:text>Id,
            </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsEnum = 'true')]">
            <xsl:text>"</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>_gt_enum_symbol": </xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
            </xsl:call-template>
            <xsl:text>Map.local_to_gt(t.</xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="Value" />
            </xsl:call-template><xsl:text>),
            </xsl:text>
    </xsl:for-each>
            <xsl:text>#
        }
        if s["</xsl:text><xsl:value-of select="$data-class-id"/><xsl:text>"] in </xsl:text>
        <xsl:value-of select="DataClass"/><xsl:text>.by_id.keys():
            dc = </xsl:text><xsl:value-of select="DataClass"/><xsl:text>.by_id[s["</xsl:text>
            <xsl:value-of select="$data-class-id"/><xsl:text>"]]
        else:
            dc = </xsl:text><xsl:value-of select="DataClass"/><xsl:text>(**s)
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: </xsl:text><xsl:value-of select="DataClass"/><xsl:text>) -> </xsl:text><xsl:value-of select="$class-name"/><xsl:text>:
        if dc is None:
            return None
        t = </xsl:text><xsl:value-of select="$class-name"/><xsl:text>(
            </xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and ((IsPrimitive = 'true') or (IsEnum = 'true'))]">
        <xsl:value-of select="Value"/><xsl:text>=dc.</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>,
            </xsl:text>
    </xsl:for-each>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsType = 'true')]">
        <xsl:value-of select="Value"/><xsl:text>Id=dc.</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>_id,
            </xsl:text>
    </xsl:for-each>
        <xsl:text>#
        )
        t.check_for_errors()
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> </xsl:text><xsl:value-of select="DataClass"/><xsl:text>:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: </xsl:text><xsl:value-of select="DataClass"/><xsl:text>) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict) -> </xsl:text><xsl:value-of select="DataClass"/><xsl:text>:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))
</xsl:text>
</xsl:if>


                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>



</xsl:stylesheet>