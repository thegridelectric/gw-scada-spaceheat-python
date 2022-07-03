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
                <xsl:variable name="alias" select="Alias"/>
                <xsl:variable name="local-alias" select="AliasRoot" />
                <xsl:variable name="schema-id" select="SchemaId" />  
                <xsl:variable name="class-name">
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="mp-schema-text" select="$local-alias" />
                    </xsl:call-template>
                </xsl:variable>

                <FileSetFile>
                            <xsl:element name="RelativePath"><xsl:text>../../../../test/schema/test_</xsl:text>
                            <xsl:value-of select="translate($local-alias,'.','_')"/><xsl:text>.py</xsl:text></xsl:element>

                    <OverwriteMode>Always</OverwriteMode>
                    <xsl:element name="FileContents">

<xsl:text>"""Tests </xsl:text><xsl:value-of select="$alias"/><xsl:text> type"""
import json

import pytest

from schema.errors import MpSchemaError
from schema.gt.</xsl:text><xsl:value-of select="translate($local-alias,'.','_')"/>
<xsl:text>.</xsl:text><xsl:value-of select="translate($local-alias,'.','_')"/><xsl:text>_maker import (
    </xsl:text>
<xsl:value-of select="$class-name"/><xsl:text>_Maker as Maker,
)


def test_</xsl:text><xsl:value-of select="translate($local-alias,'.','_')"/>
<xsl:text>():

    gw_dict = {</xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and ((not (IsEnum = 'true') and normalize-space(SubTypeDataClass) = '') or (IsList = 'true'))]">
        <xsl:text>
        "</xsl:text><xsl:value-of select="Value"  />
        <xsl:text>": </xsl:text>
        <xsl:value-of select="normalize-space(TestValue)"/>
        <xsl:text>,</xsl:text>
        </xsl:for-each>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsEnum = 'true') and not (IsList = 'true')]">
        <xsl:text>
        "</xsl:text><xsl:value-of select="Value"  />
        <xsl:text>GtEnumSymbol": </xsl:text>
        <xsl:value-of select="normalize-space(TestValue)"/>
            <xsl:text>,</xsl:text>
        </xsl:for-each>

        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (normalize-space(SubTypeDataClass) != '')and  not (IsList = 'true')]">
        <xsl:text>
        "</xsl:text><xsl:value-of select="Value"  />
        <xsl:text>Id": </xsl:text>
        <xsl:value-of select="normalize-space(TestValue)"/>
        <xsl:text>,</xsl:text>
        </xsl:for-each>
    <xsl:text>
        "TypeAlias": "</xsl:text><xsl:value-of select="$alias"/><xsl:text>",
    }

    with pytest.raises(MpSchemaError):
        Maker.type_to_tuple(gw_dict)

    with pytest.raises(MpSchemaError):
        Maker.type_to_tuple('"not a dict"')

    # Test type_to_tuple
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)

    # test type_to_tuple and tuple_to_type maps
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple

    # test Maker init
    t = Maker(
        </xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)]">
        <xsl:if test="(normalize-space(SubTypeDataClass) = '') ">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>=gw_tuple.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>,
        </xsl:text>
        </xsl:if>
        <xsl:if test="(normalize-space(SubTypeDataClass) != '') ">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>_id=gw_tuple.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>Id,
        </xsl:text>
        </xsl:if>
        </xsl:for-each>
        <xsl:text>#
    ).tuple
    assert t == gw_tuple

    </xsl:text>
    <xsl:if test="MakeDataClass='true'">
    <xsl:text>######################################
    # Dataclass related tests
    ######################################

    dc = Maker.tuple_to_dc(gw_tuple)
    assert gw_tuple == Maker.dc_to_tuple(dc)
    assert Maker.type_to_dc(Maker.dc_to_type(dc)) == dc

    </xsl:text>
    </xsl:if>
    <xsl:text>######################################
    # MpSchemaError raised if missing a required attribute
    ######################################

    orig_value = gw_dict["TypeAlias"]
    del gw_dict["TypeAlias"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = orig_value

    </xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (IsRequired='true') ]">
    <xsl:if test = "((not (IsEnum = 'true') and normalize-space(SubTypeDataClass) = '') or (IsList = 'true'))">
    <xsl:text>orig_value = gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>"]
    del gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/>
    <xsl:text>"] = orig_value

    </xsl:text>
    </xsl:if>
    <xsl:if test = "((IsEnum = 'true') and not (IsList = 'true'))">
    <xsl:text>orig_value = gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>GtEnumSymbol"]
    del gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>GtEnumSymbol"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/>
    <xsl:text>GtEnumSymbol"] = orig_value

    </xsl:text>
    </xsl:if>
    <xsl:if test = "((normalize-space(SubTypeDataClass) != '') and not (IsList = 'true'))">
    <xsl:text>orig_value = gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>Id"]
    del gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>Id"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/>
    <xsl:text>Id"] = orig_value

    </xsl:text>
    </xsl:if>
    
    </xsl:for-each>

    <xsl:if test="count($airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not (IsRequired='true')]) > 0">
    <xsl:text>######################################
    # Optional attributes can be removed from type
    ######################################

    </xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not (IsRequired='true')]">
    <xsl:if test= "(normalize-space(SubTypeDataClass) != '')">
    <xsl:text>orig_value = gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>Id"]
    del gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>Id"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["</xsl:text><xsl:value-of  select="Value"/>
    <xsl:text>Id"] = orig_value

    </xsl:text>
    </xsl:if>
    <xsl:if  test= "(normalize-space(SubTypeDataClass) = '')">
    <xsl:text>orig_value = gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>"]
    del gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>"]
    gw_type = json.dumps(gw_dict)
    gw_tuple = Maker.type_to_tuple(gw_type)
    assert Maker.type_to_tuple(Maker.tuple_to_type(gw_tuple)) == gw_tuple
    gw_dict["</xsl:text><xsl:value-of  select="Value"/>
    <xsl:text>"] = orig_value

    </xsl:text>
    </xsl:if>
    </xsl:for-each>
    </xsl:if>
    <xsl:text>######################################
    # MpSchemaError raised if attributes have incorrect type
    ######################################

    </xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id)]">
    <xsl:variable name="attribute"><xsl:value-of select="Value"/></xsl:variable>

    <xsl:if test = "(normalize-space(SubTypeDataClass) != '')">
        <xsl:text>orig_value = gw_dict["</xsl:text>
        <xsl:value-of  select="Value"/><xsl:text>Id"]
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>Id"] = "Not a dataclass id"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>Id"] = orig_value

    </xsl:text>
    </xsl:if>
    <xsl:if test= "not(IsList = 'true') and (IsType='true') and (normalize-space(SubTypeDataClass) = '') ">
    <xsl:text>orig_value = gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>"]
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = "Not a </xsl:text>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
    </xsl:call-template><xsl:text>."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            </xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not(Value=$attribute)]">
        <xsl:if test="(normalize-space(SubTypeDataClass) = '') ">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>=gw_tuple.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>,
            </xsl:text>
        </xsl:if>
        <xsl:if test="(normalize-space(SubTypeDataClass) != '') ">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>_id=gw_tuple.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>Id,
            </xsl:text>
        </xsl:if>
        </xsl:for-each>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="$attribute"  />
        </xsl:call-template>
        <xsl:text>="Not a </xsl:text>
        <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                </xsl:call-template><xsl:text>",
        )

    </xsl:text>
    </xsl:if>
    <xsl:if test= "not(IsList = 'true') and (IsPrimitive='true') ">
   
    <xsl:text>orig_value = gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>"]
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = </xsl:text>
            <xsl:if test = "PrimitiveType='Integer'">
            <xsl:text>1.1
    </xsl:text>
            </xsl:if>
            <xsl:if test = "PrimitiveType='Number'">
            <xsl:text>"This string is not a float."
    </xsl:text>
            </xsl:if>
            <xsl:if test = "PrimitiveType='Boolean'">
            <xsl:text>"This string is not a boolean."
    </xsl:text>
            </xsl:if>
            <xsl:if test = "PrimitiveType='String'">
            <xsl:text>42
    </xsl:text>
            </xsl:if>
    <xsl:text>with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = orig_value

    </xsl:text>
    </xsl:if>
    <xsl:if test = "not (IsList = 'true') and IsEnum = 'true'">
    
    <xsl:text>with pytest.raises(MpSchemaError):
        Maker(
            </xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not(Value=$attribute)]">
        <xsl:if test="(normalize-space(SubTypeDataClass) = '') ">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>=gw_tuple.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>,
            </xsl:text>
        </xsl:if>
        <xsl:if test="(normalize-space(SubTypeDataClass) != '') ">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>_id=gw_tuple.</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>Id,
            </xsl:text>
        </xsl:if>
        </xsl:for-each>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="$attribute"  />
        </xsl:call-template>
        <xsl:text>="This is not a </xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
        </xsl:call-template><xsl:text> Enum.",
        )

    </xsl:text>
    
    </xsl:if>
    <xsl:if test= "(IsList = 'true') and (IsType='true') ">
    <xsl:text>orig_value = gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>"]
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = "Not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = orig_value

    orig_value = gw_dict["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>"]
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = ["Not even a dict"]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)

    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = [{"Failed": "Not a GtSimpleSingleStatus"}]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = orig_value

    with pytest.raises(MpSchemaError):
        Maker(
            </xsl:text>
        <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not(Value=$attribute)]">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>=gw_dict["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"],
            </xsl:text>
        </xsl:for-each>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="$attribute"  />
            </xsl:call-template>
              <xsl:text>=["Not a </xsl:text>
                <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                </xsl:call-template>
                <xsl:text>"],
        )

    with pytest.raises(MpSchemaError):
        Maker(
            </xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not(Value=$attribute)]">
    <xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="Value"  />
    </xsl:call-template>
    <xsl:text>=gw_tuple.</xsl:text>
    <xsl:value-of select="Value"/>
    <xsl:text>,
            </xsl:text>
    </xsl:for-each>
    <xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="$attribute"  />
    </xsl:call-template>
    <xsl:text>="This string is not a list",
        )

    </xsl:text>
        </xsl:if>
    <xsl:if test = "(IsList = 'true') and (IsPrimitive = 'true')">
        <xsl:text>orig_value = gw_dict["</xsl:text>
        <xsl:value-of  select="Value"/><xsl:text>"]
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = "This string is not a list."
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = </xsl:text>
            <xsl:if test = "IsEnum = 'true'">
            <xsl:text>["This string is not a </xsl:text>
                <xsl:call-template name="nt-case">
                    <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
                </xsl:call-template>
                <xsl:text>GtEnumSymbol."]
    </xsl:text>
            </xsl:if>
            <xsl:if test = "IsPrimitive='true'">
                <xsl:if test = "PrimitiveType='Integer'">
            <xsl:text>[1.1]
    </xsl:text>
                </xsl:if>
                <xsl:if test = "PrimitiveType='Number'">
            <xsl:text>["This string is not a float."]
    </xsl:text>
                </xsl:if>
                <xsl:if test = "PrimitiveType='Boolean'">
            <xsl:text>["This string is not a boolean."]
    </xsl:text>
                </xsl:if>
                <xsl:if test = "PrimitiveType='String'">
            <xsl:text>[42]
    </xsl:text>
                </xsl:if>
            </xsl:if>
        <xsl:text>with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of  select="Value"/><xsl:text>"] = orig_value

    </xsl:text>
    </xsl:if>
    <xsl:if test = "(IsList = 'true') and (IsEnum= 'true')">

    <xsl:text>with pytest.raises(MpSchemaError):
        Maker(
            </xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not(Value=$attribute)]">
    <xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="Value"  />
    </xsl:call-template>
    <xsl:text>=gw_tuple.</xsl:text>
    <xsl:value-of select="Value"/>
    <xsl:text>,
            </xsl:text>
    </xsl:for-each>
    <xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="$attribute"  />
    </xsl:call-template>
    <xsl:text>="This string is not a list",
        )

    with pytest.raises(MpSchemaError):
        Maker(
            </xsl:text>
    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and not(Value=$attribute)]">
    <xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="Value"  />
    </xsl:call-template>
    <xsl:text>=gw_tuple.</xsl:text>
    <xsl:value-of select="Value"/>
    <xsl:text>,
            </xsl:text>
    </xsl:for-each>
    <xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="$attribute"  />
    </xsl:call-template>
    <xsl:text>=["This is not a </xsl:text>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="mp-schema-text" select="EnumLocalName" />
    </xsl:call-template><xsl:text> Enum."],
        )

    </xsl:text>
    </xsl:if>
    
    </xsl:for-each>

    <xsl:text>######################################
    # MpSchemaError raised if TypeAlias is incorrect
    ######################################

    gw_dict["TypeAlias"] = "not the type alias"
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["TypeAlias"] = "</xsl:text><xsl:value-of select="$alias"/><xsl:text>"
</xsl:text>    
    <xsl:if test="count($airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (normalize-space(PrimitiveFormatFail1) != '')]) > 0">

<xsl:text>
    ######################################
    # MpSchemaError raised if primitive attributes do not have appropriate property_format
    ######################################</xsl:text>

    <xsl:for-each select="$airtable//SchemaAttributes/SchemaAttribute[(GtSchema = $schema-id) and (normalize-space(PrimitiveFormatFail1) != '')]">
    <xsl:if test="not (IsList='true')">
    <xsl:text>

    gw_dict["</xsl:text>
    <xsl:value-of select="Value"/>
    <xsl:text>"] = </xsl:text>
    <xsl:value-of select="normalize-space(PrimitiveFormatFail1)"/><xsl:text>
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] = </xsl:text>
    <xsl:value-of select="normalize-space(TestValue)"/>
    </xsl:if>

    <xsl:if test="(IsList='true')">
    <xsl:text>

    gw_dict["</xsl:text>
    <xsl:value-of select="Value"/>
    <xsl:text>"] = [</xsl:text>
    <xsl:value-of select="normalize-space(PrimitiveFormatFail1)"/><xsl:text>]
    with pytest.raises(MpSchemaError):
        Maker.dict_to_tuple(gw_dict)
    gw_dict["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] = </xsl:text>
    <xsl:value-of select="normalize-space(TestValue)"/>
    </xsl:if>
    </xsl:for-each>

    <xsl:text>

    # End of Test
</xsl:text>
</xsl:if>

                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>



</xsl:stylesheet>