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
    <xsl:include href="GnfCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
        <FileSet>
            <FileSetFiles>
                <xsl:for-each select="$airtable//ProtocolTypes/ProtocolType[(normalize-space(ProtocolName) ='scada')]">
                <xsl:variable name="versioned-type-id" select="VersionedType"/>
                <xsl:for-each select="$airtable//VersionedTypes/VersionedType[(VersionedTypeId = $versioned-type-id)  and (Status = 'Active' or Status = 'Pending') and (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial')]">
                <xsl:variable name="type-name" select="TypeName"/>
                <xsl:variable name="class-name">
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="type-name-text" select="$type-name" />
                    </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="overwrite-mode">

                    <xsl:if test="not (Status = 'Pending')">
                    <xsl:text>Never</xsl:text>
                    </xsl:if>
                    <xsl:if test="(Status = 'Pending')">
                    <xsl:text>Always</xsl:text>
                    </xsl:if>
                    </xsl:variable>
                <FileSetFile>
                            <xsl:element name="RelativePath"><xsl:text>../../../../tests/types/test_</xsl:text>
                            <xsl:value-of select="translate($type-name,'.','_')"/><xsl:text>.py</xsl:text></xsl:element>

                    <OverwriteMode><xsl:value-of select="$overwrite-mode"/></OverwriteMode>
                    <xsl:element name="FileContents">

<xsl:text>"""Tests </xsl:text><xsl:value-of select="$type-name"/><xsl:text> type, version </xsl:text>
<xsl:value-of select="Version"/>
<xsl:text>"""
import json

import pytest
from pydantic import ValidationError

from gridworks.errors import SchemaError</xsl:text>
<xsl:choose>
<xsl:when test="(NotInInit='true')">
<xsl:text>
from gwtypes.</xsl:text><xsl:value-of select="translate($type-name,'.','_')"/>
<xsl:text> import </xsl:text>
<xsl:value-of select="$class-name"/><xsl:text>_Maker as Maker</xsl:text>
</xsl:when>

<xsl:otherwise>
<xsl:text>
from gwtypes import </xsl:text>
<xsl:value-of select="$class-name"/><xsl:text>_Maker as Maker</xsl:text>
</xsl:otherwise>

</xsl:choose>
<xsl:for-each select="$airtable//GtEnums/GtEnum[(normalize-space(Name) !='')  and (count(TypesThatUse[text()=$versioned-type-id])>0)]">
<xsl:text>
from enums import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="LocalName" />
</xsl:call-template>
</xsl:for-each>
<xsl:text>


def test_</xsl:text><xsl:value-of select="translate($type-name,'.','_')"/>
<xsl:text>_generated() -> None:
    d = {</xsl:text>
        <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
        <xsl:sort select="Idx" data-type="number"/>
        <xsl:variable name = "attribute-name">
        <xsl:value-of select="Value"/>
        <!-- If attribute is associated to a data class, add Id to the Attribute name-->
        <xsl:if test="not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
        <xsl:text>Id</xsl:text>
        </xsl:if>
        </xsl:variable>

        <xsl:if test="(not (IsEnum = 'true')) or (IsList = 'true')">
        <xsl:text>
        "</xsl:text><xsl:value-of select="$attribute-name"  />
        <xsl:text>": </xsl:text>
        <xsl:value-of select="normalize-space(TestValue)"/>
        <xsl:text>,</xsl:text>
        </xsl:if>

        <xsl:if test="(IsEnum = 'true') and not (IsList = 'true')">
        <xsl:text>
        "</xsl:text><xsl:value-of select="Value"  />
        <xsl:text>GtEnumSymbol": </xsl:text>
        <xsl:value-of select="normalize-space(TestValue)"/>
            <xsl:text>,</xsl:text>
        </xsl:if>



        </xsl:for-each>
    <xsl:text>
        "TypeName": "</xsl:text><xsl:value-of select="$type-name"/><xsl:text>",
        "Version": "</xsl:text><xsl:value-of select="Version"/><xsl:text>",
    }

    with pytest.raises(SchemaError):
        Maker.type_to_tuple(d)

    with pytest.raises(SchemaError):
        Maker.type_to_tuple('"not a dict"')

    # Test type_to_tuple
    gtype = json.dumps(d)
    gtuple = Maker.type_to_tuple(gtype)

    # test type_to_tuple and tuple_to_type maps
    assert Maker.type_to_tuple(Maker.tuple_to_type(gtuple)) == gtuple

    # test Maker init
    t = Maker(
        </xsl:text>
        <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
        <xsl:sort select="Idx" data-type="number"/>
        <xsl:variable name = "attribute-name">
        <xsl:value-of select="Value"/>
        <!-- If attribute is associated to a data class, add Id to the Attribute name-->
        <xsl:if test="not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
        <xsl:text>Id</xsl:text>
        </xsl:if>
        </xsl:variable>

        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="$attribute-name"  />
        </xsl:call-template>
        <xsl:text>=gtuple.</xsl:text>
        <xsl:value-of select="$attribute-name"/>
        <xsl:text>,
        </xsl:text>
        </xsl:for-each>
        <xsl:text>
    ).tuple
    assert t == gtuple

    </xsl:text>
    <xsl:if test="MakeDataClass='true'">
    <xsl:text>######################################
    # Dataclass related tests
    ######################################

    dc = Maker.tuple_to_dc(gtuple)
    assert gtuple == Maker.dc_to_tuple(dc)
    assert Maker.type_to_dc(Maker.dc_to_type(dc)) == dc

    </xsl:text>
    </xsl:if>
    <xsl:text>######################################
    # SchemaError raised if missing a required attribute
    ######################################

    d2 = dict(d)
    del d2["TypeName"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    </xsl:text>
    <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and (IsRequired='true') ]">
    <xsl:sort select="Idx" data-type="number"/>

    <xsl:if test = "((not (IsEnum = 'true')) or (IsList = 'true')) ">



    <xsl:text>d2 = dict(d)
    del d2["</xsl:text>
    <xsl:value-of  select="Value"/>
        <xsl:if test="not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
        <xsl:text>Id</xsl:text>
        </xsl:if>

    <xsl:text>"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    </xsl:text>
    </xsl:if>


    <xsl:if test = "((IsEnum = 'true') and not (IsList = 'true'))">
    <xsl:text>d2 = dict(d)
    del d2["</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>GtEnumSymbol"]
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    </xsl:text>
    </xsl:if>


    </xsl:for-each>

    <xsl:if test="count($airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and not (IsRequired='true')]) > 0">
    <xsl:text>######################################
    # Optional attributes can be removed from type
    ######################################

    </xsl:text>
    <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and not (IsRequired='true')]">
    <xsl:sort select="Idx" data-type="number"/>

    <xsl:if test= "(normalize-space(SubTypeDataClass) != '')">
    <xsl:text>d2 = dict(d)
    if "</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>Id" in d2.keys():
        del d2["</xsl:text>
        <xsl:value-of  select="Value"/><xsl:text>Id"]
    Maker.dict_to_tuple(d2)

    </xsl:text>
    </xsl:if>

    <xsl:if  test= "(normalize-space(SubTypeDataClass) = '')">
    <xsl:text>d2 = dict(d)
    if "</xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>" in d2.keys():
        del d2["</xsl:text>
        <xsl:value-of  select="Value"/><xsl:text>"]
    Maker.dict_to_tuple(d2)

    </xsl:text>
    </xsl:if>
    </xsl:for-each>
    </xsl:if>
    <xsl:text>######################################
    # Behavior on incorrect types
    ######################################</xsl:text>
    <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
    <xsl:sort select="Idx" data-type="number"/>
    <xsl:variable name="attribute"><xsl:value-of select="Value"/></xsl:variable>

    <xsl:if test= "(IsPrimitive='true') and not(IsList = 'true')">

        <xsl:if test = "PrimitiveType='Integer'">
    <xsl:text>

    d2 = dict(d, </xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>="</xsl:text>
         <xsl:value-of select="TestValue"/><xsl:text>.1")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)</xsl:text>
        </xsl:if>

        <xsl:if test = "PrimitiveType='Number'">
    <xsl:text>

    d2 = dict(d, </xsl:text>
        <xsl:value-of  select="Value"/><xsl:text>="this is not a float")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)</xsl:text>
        </xsl:if>

        <xsl:if test = "PrimitiveType='Boolean'">
    <xsl:text>

    d2 = dict(d, </xsl:text>
        <xsl:value-of  select="Value"/><xsl:text>="this is not a boolean")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)</xsl:text>
        </xsl:if>
    </xsl:if>


    <xsl:if test = "(IsEnum = 'true') and not (IsList = 'true')">
    <xsl:text>

    d2 = dict(d, </xsl:text>
    <xsl:value-of select="Value"/>
    <xsl:text>GtEnumSymbol="unknown_symbol")
    Maker.dict_to_tuple(d2).</xsl:text>
    <xsl:value-of select="Value"/>
    <xsl:text> == </xsl:text>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="type-name-text" select="EnumLocalName" />
    </xsl:call-template>
    <xsl:text>.default()</xsl:text>
    </xsl:if>


    <xsl:if test= "(IsType='true')  and (IsList = 'true')">
    <xsl:text>

    d2  = dict(d, </xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>="Not a list.")
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, </xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>=["Not a list of dicts"])
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)

    d2  = dict(d, </xsl:text>
    <xsl:value-of  select="Value"/><xsl:text>= [{"Failed": "Not a GtSimpleSingleStatus"}])
    with pytest.raises(SchemaError):
        Maker.dict_to_tuple(d2)</xsl:text>
        </xsl:if>

    </xsl:for-each>

    <xsl:text>

    ######################################
    # SchemaError raised if TypeName is incorrect
    ######################################

    d2 = dict(d, TypeName="not the type name")
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)
</xsl:text>
    <xsl:if test="count($airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and (normalize-space(PrimitiveFormatFail1) != '')]) > 0">

<xsl:text>
    ######################################
    # SchemaError raised if primitive attributes do not have appropriate property_format
    ######################################</xsl:text>

    <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and (normalize-space(PrimitiveFormatFail1) != '')]">
    <xsl:sort select="Idx" data-type="number"/>

    <xsl:if test="not (IsList='true')">
    <xsl:text>

    d2 = dict(d, </xsl:text>
    <xsl:value-of select="Value"/>
    <xsl:text>=</xsl:text>
    <xsl:value-of select="normalize-space(PrimitiveFormatFail1)"/><xsl:text>)
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)</xsl:text>
    </xsl:if>

    <xsl:if test="(IsList='true')">
    <xsl:text>

    d2 = dict(d, </xsl:text>
    <xsl:value-of select="Value"/>
    <xsl:text>=[</xsl:text>
    <xsl:value-of select="normalize-space(PrimitiveFormatFail1)"/><xsl:text>])
    with pytest.raises(ValidationError):
        Maker.dict_to_tuple(d2)</xsl:text>

    </xsl:if>
    </xsl:for-each>

<!-- Add newline at EOF for git and pre-commit-->
<xsl:text>&#10;</xsl:text>
</xsl:if>

                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>
                </xsl:for-each>
            </FileSetFiles>
        </FileSet>
    </xsl:template>



</xsl:stylesheet>
