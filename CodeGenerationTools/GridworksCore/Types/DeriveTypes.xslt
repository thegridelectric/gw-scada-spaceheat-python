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
                <xsl:for-each select="$airtable//VersionedTypes/VersionedType[(VersionedTypeId = $versioned-type-id)  and (Status = 'Active' or Status = 'Pending') and (ProtocolCategory= 'Json' or ProtocolCategory = 'GwAlgoSerial')]">
                <xsl:variable name="type-name" select="TypeName" />
                <xsl:variable name="total-attributes" select="count($airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)])" />
                <xsl:variable name="versioned-type-name" select="VersionedTypeName"/>
                <xsl:variable name="python-class-name">
                    <xsl:if test="(normalize-space(PythonClassName) ='')">
                    <xsl:call-template name="nt-case">
                        <xsl:with-param name="type-name-text" select="TypeName" />
                    </xsl:call-template>
                    </xsl:if>
                    <xsl:if test="(normalize-space(PythonClassName) != '')">
                    <xsl:value-of select="normalize-space(PythonClassName)" />
                    </xsl:if>
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
                                <xsl:element name="RelativePath"><xsl:text>../../../gw_spaceheat/gwtypes/</xsl:text>
                                <xsl:value-of select="translate($type-name,'.','_')"/><xsl:text>.py</xsl:text></xsl:element>

                        <OverwriteMode><xsl:value-of select="$overwrite-mode"/></OverwriteMode>
                        <xsl:element name="FileContents">


<xsl:text>"""Type </xsl:text><xsl:value-of select="$type-name"/><xsl:text>, version </xsl:text>
<xsl:value-of select="Version"/><xsl:text>"""
import json
import logging
from typing import Any, Dict</xsl:text>
<xsl:if test="count($airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and (IsList = 'true')])>0">
<xsl:text>, List</xsl:text>
</xsl:if>
<xsl:text>, Literal</xsl:text>

<xsl:if test="count($airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and not (IsRequired = 'true')]) > 0">
<xsl:text>, Optional</xsl:text>
</xsl:if>
<xsl:text>

from gridworks.errors import SchemaError
from pydantic import BaseModel</xsl:text>
<xsl:if test="ExtraAllowed='true'">
<xsl:text>, Extra</xsl:text>

</xsl:if>
<xsl:text>, Field</xsl:text>
<xsl:if test="count($airtable//TypeAxioms/TypeAxiom[MultiPropertyAxiom=$versioned-type-id]) > 0">
<xsl:text>, root_validator</xsl:text>
</xsl:if>
<xsl:if test="count($airtable//TypeAttributes/TypeAttribute[
    (VersionedType = $versioned-type-id) and
        (
            (IsList='true' and PrimitiveType != '' and normalize-space(Format) != '') or
            (normalize-space(PrimitiveFormat) != '') or 
            (Axiom != '') or 
            (normalize-space(SubTypeDataClass) != '' and not(IsList='true'))
	    )
]) > 0">
<xsl:text>, validator</xsl:text>
</xsl:if>




<xsl:if test="MakeDataClass='true'">
<xsl:if test="not(IsComponent = 'true') and not(IsCac = 'true')">
<xsl:text>
from data_classes.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(DataClass,'.','_')"  />
</xsl:call-template>
<xsl:text> import </xsl:text><xsl:value-of select="DataClass"/>

</xsl:if>
</xsl:if>
<xsl:if test="IsComponent = 'true'">
<xsl:text>
from data_classes.components.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(DataClass,'.','_')"  />
</xsl:call-template>
<xsl:text> import </xsl:text><xsl:value-of select="DataClass"/>
</xsl:if>


<xsl:if test="IsCac = 'true'">
<xsl:text>
from data_classes.cacs.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(DataClass,'.','_')"  />
</xsl:call-template>
<xsl:text> import </xsl:text><xsl:value-of select="DataClass"/>
</xsl:if>

<xsl:if test="count($airtable//TypeAttributes/TypeAttribute[
    (VersionedType = $versioned-type-id) and
    (IsType = 'true') and 
    (normalize-space(SubTypeDataClass) = '' or IsList = 'true')]) 
    > 0">
<xsl:text>

# sub-types</xsl:text>
</xsl:if>

<xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">

<!-- When the attribute is a subtype (and not a singleton object associated to a dataclass, in which case it just gets a pointer) -->
<xsl:if test="(IsType = 'true') and (normalize-space(SubTypeDataClass) = '' or IsList = 'true')">


<!-- Being careful to avoid circular references-->
<xsl:choose>

<!-- For a type native to SCADA that apparently provokes a circular reference when added to init: refer to the whole thing-->
<xsl:when test="(NotInInit='true') and count(Protocols[text()='scada']) > 0" >
<xsl:text>
from gwtypes.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(SubTypeName,'.','_')"  />
</xsl:call-template>
<xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="SubTypeName" />
</xsl:call-template><xsl:text>
from gwtypes.</xsl:text>
<xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(SubTypeName,'.','_')"  />
</xsl:call-template>
<xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="SubTypeName" />
</xsl:call-template><xsl:text>_Maker</xsl:text>
</xsl:when>

<!-- Else the types are referenced in the scada gwtype init-->
<xsl:otherwise>
<xsl:text>
from gwtypes import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="SubTypeName" />
</xsl:call-template><xsl:text>, </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="SubTypeName" />
</xsl:call-template><xsl:text>_Maker</xsl:text>

</xsl:otherwise>
</xsl:choose>

<!-- End of subtype if-->
</xsl:if>


</xsl:for-each>

<xsl:if test="count($airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and (IsEnum='true')]) > 0">
<xsl:text>

# enums</xsl:text>
</xsl:if>

<xsl:for-each select="$airtable//GtEnums//GtEnum[normalize-space(Name) !='']">
<xsl:sort select="Name" data-type="text"/>

<xsl:variable name="base-name" select="LocalName"/>
<xsl:variable name="enum-local-name">
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="LocalName" />
</xsl:call-template>
</xsl:variable>
<xsl:if test="count($airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and (EnumLocalName[text() = $base-name])])>0">

<xsl:text>
from enums import </xsl:text>
<xsl:value-of select="$enum-local-name"/>
<xsl:if test="count($airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and (UseEnumAlias= 'true') and (EnumLocalName[text()=$base-name])])>0">
<xsl:text> as Enum</xsl:text>
<xsl:value-of select="$enum-local-name"/>
</xsl:if>

</xsl:if>

</xsl:for-each>


<xsl:text>

LOG_FORMAT = (
    "%(levelname) -10s %(asctime)s %(name) -30s %(funcName) "
    "-35s %(lineno) -5d: %(message)s"
)
LOGGER = logging.getLogger(__name__)


class </xsl:text>
<xsl:value-of select="$python-class-name"/>
<xsl:text>(BaseModel):
    """
    </xsl:text>
    <!-- One line title, if it exists -->
    <xsl:if test="(normalize-space(Title) != '')">
        <xsl:value-of select="Title"/>
            <!-- With a space before the Description (if description exists)-->
            <xsl:if test="(normalize-space(Description) != '')">
                <xsl:text>.

    </xsl:text>
            </xsl:if>
    </xsl:if>

    <!-- Type Description, wrapped, if it exists -->
    <xsl:if test="(normalize-space(Description) != '')">
    <xsl:call-template name="wrap-text">
        <xsl:with-param name="text" select="normalize-space(Description)"/>
        <xsl:with-param name="indent-spaces" select="4"/>
    </xsl:call-template>
    </xsl:if>

    <xsl:if test="(normalize-space(Url) != '')">
    <xsl:text>

    [More info](</xsl:text>
        <xsl:value-of select="normalize-space(Url)"/>
        <xsl:text>)</xsl:text>
    </xsl:if>
    <xsl:text>
    """

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

<xsl:variable name="enum-class-name">
    <xsl:if test = "(IsEnum = 'true')">
        <xsl:if test="UseEnumAlias = 'true'">
        <xsl:text>Enum</xsl:text>
        </xsl:if>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="type-name-text" select="EnumLocalName" />
        </xsl:call-template>
    </xsl:if>
</xsl:variable>

<xsl:variable name="attribute-type">

    <!-- If Optional, start the Optional bracket-->
    <xsl:if test="not(IsRequired = 'true')">
    <xsl:text>Optional[</xsl:text>
    </xsl:if>

    <!-- If List, start the List bracket-->
    <xsl:if test="IsList = 'true'">
    <xsl:text>List[</xsl:text>
    </xsl:if>
    <xsl:choose>
    <xsl:when test="(IsPrimitive = 'true')">
    <xsl:call-template name="python-type">
        <xsl:with-param name="gw-type" select="PrimitiveType"/>
    </xsl:call-template>
    </xsl:when>

    <xsl:when test = "(IsEnum = 'true')">
        <xsl:value-of select="$enum-class-name"/>
    </xsl:when>

    <!-- If Attribute is a type associated with a dataclass, the reference is to its id, which is a string -->
    <xsl:when test = "not(normalize-space(SubTypeDataClass) = '') and not(IsList = 'true')">
    <xsl:text>str</xsl:text>
    </xsl:when>

    <!-- Otherwise, the reference is to the type  -->
    <xsl:when test="(IsType = 'true')">
        <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="SubTypeName" />
        </xsl:call-template>
    </xsl:when>
    <xsl:otherwise></xsl:otherwise>
    </xsl:choose>
            <!-- If List, end the List bracket-->
    <xsl:if test="IsList = 'true'">
    <xsl:text>]</xsl:text>
    </xsl:if>

    <!-- If Optional, end the Optional bracket-->
    <xsl:if test="not(IsRequired = 'true')">
    <xsl:text>]</xsl:text>
    </xsl:if>
</xsl:variable>

    <xsl:call-template name="insert-spaces"/>

     <!-- Name of the attribute -->
    <xsl:value-of select="$attribute-name"/><xsl:text>: </xsl:text>

    <!-- Add the attribute type (works for primitive, enum, subtype)-->
    <xsl:value-of select="$attribute-type"/>


<xsl:text> = </xsl:text>

<xsl:text>Field(
        title="</xsl:text>
        <xsl:if test="normalize-space(Title)!=''">
        <xsl:value-of select="Title"/>
        </xsl:if>
        <xsl:if test="normalize-space(Title)=''">
        <xsl:value-of select="Value"/>
        </xsl:if>
        <xsl:text>",</xsl:text>

    <!-- Add a description if either Description or URL have content -->
    <xsl:if test="(normalize-space(Description) !='') or (normalize-space(Url) != '')">

        <xsl:choose>
        <xsl:when test="(string-length(normalize-space(Description)) > 78) or ((normalize-space(Description) !='') and (normalize-space(Url) != ''))">
        <!-- For a long description, or when there is a description AND a URL  -->
        <xsl:text>
        description=(
            "</xsl:text>
        <xsl:call-template name="wrap-quoted-text">
            <xsl:with-param name="text" select="normalize-space(Description)"/>
            <xsl:with-param name="indent-spaces" select="12"/>
        </xsl:call-template>
        <xsl:text>"</xsl:text>
        <xsl:if test = "(normalize-space(Url) != '')">
        <xsl:text>
            "[More info](</xsl:text>
        <xsl:value-of select="normalize-space(Url)"/>
        <xsl:text>)"</xsl:text>
        </xsl:if>
        <xsl:text>
        ),</xsl:text>

        </xsl:when>

         <xsl:when test="normalize-space(Description) !=''">
        <!-- When there is a short non-empty description and no URL -->
        <xsl:text>
        description="</xsl:text>
        <xsl:value-of select="normalize-space(Description)"/>
        <xsl:text>",</xsl:text>
        </xsl:when>

         <xsl:when test="normalize-space(Url) !=''">
        <!-- When there is a URL only -->
        <xsl:text>
        description="</xsl:text>
        <xsl:text>[More info](</xsl:text>
        <xsl:value-of select="normalize-space(Url)"/>
        <xsl:text>)",</xsl:text>
        </xsl:when>

        <xsl:otherwise>
        <!-- When there is no URL and no Description, do not include description in the Field -->
        </xsl:otherwise>

        </xsl:choose>

    </xsl:if>

<!-- SETTING DEFAULT VALUE FOR ATTRIBUTE IN CLASS DECLARATION -->
    <xsl:choose>

    <!-- If the attribute is not required, choose the default to always be none-->
    <xsl:when test= "not (IsRequired = 'true')">
    <xsl:text>
        default=None,</xsl:text>
    </xsl:when>

    <!-- Else if a default value is specified, use that -->
    <xsl:when test="(normalize-space(DefaultValue) !='')">
        <xsl:text>
        default=</xsl:text>
         <xsl:if test="IsEnum='true'">
             <xsl:call-template name="nt-case">
                    <xsl:with-param name="type-name-text" select="EnumLocalName" />
            </xsl:call-template><xsl:text>.</xsl:text>
         </xsl:if>
        <xsl:value-of select="DefaultValue"/>
        <xsl:text>,</xsl:text>
    </xsl:when>
    <xsl:otherwise>
    </xsl:otherwise>
    </xsl:choose>

    <xsl:text>
    )
</xsl:text>
<!-- End of declaring the attributes of the class-->
</xsl:for-each>


<xsl:text>    TypeName: Literal["</xsl:text><xsl:value-of select="TypeName"/><xsl:text>"] = "</xsl:text><xsl:value-of select="TypeName"/><xsl:text>"
    Version: Literal["</xsl:text>
<xsl:value-of select="Version"/><xsl:text>"] = "</xsl:text><xsl:value-of select="Version"/><xsl:text>"</xsl:text>

<xsl:if test="ExtraAllowed='true'"><xsl:text>

    class Config:
        extra = Extra.allow</xsl:text>
</xsl:if>

<!-- CONSTRUCTING VALIDATORS CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS -->
<!-- CONSTRUCTING VALIDATORS CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS -->
<!-- CONSTRUCTING VALIDATORS CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS -->
<!-- CONSTRUCTING VALIDATORS CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS  CONSTRUCTING VALIDATORS -->

    <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
    <xsl:sort select="Idx" data-type="number"/>
    <xsl:variable name="type-attribute-id" select="TypeAttributeId" />

    <xsl:variable name="enum-class-name">
        <xsl:if test = "(IsEnum = 'true')">
            <xsl:if test="UseEnumAlias = 'true'">
            <xsl:text>Enum</xsl:text>
            </xsl:if>
            <xsl:call-template name="nt-case">
                            <xsl:with-param name="type-name-text" select="EnumLocalName" />
            </xsl:call-template>
        </xsl:if>
    </xsl:variable>

    <xsl:variable name="attribute-type">

        <!-- If Optional, start the Optional bracket-->
        <xsl:if test="not(IsRequired = 'true')">
        <xsl:text>Optional[</xsl:text>
        </xsl:if>

        <!-- If List, start the List bracket-->
        <xsl:if test="IsList = 'true'">
        <xsl:text>List[</xsl:text>
        </xsl:if>
        <xsl:choose>
        <xsl:when test="(IsPrimitive = 'true')">
        <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="PrimitiveType"/>
        </xsl:call-template>
        </xsl:when>

        <xsl:when test = "(IsEnum = 'true')">
            <xsl:value-of select="$enum-class-name"/>
        </xsl:when>

        <!-- If Attribute is a type associated with a dataclass, the reference is to its id, which is a string -->
        <xsl:when test = "not(normalize-space(SubTypeDataClass) = '')">
        <xsl:text>str</xsl:text>
        </xsl:when>

        <!-- Otherwise, the reference is to the type  -->
        <xsl:when test="(IsType = 'true')">
            <xsl:call-template name="nt-case">
                <xsl:with-param name="type-name-text" select="SubTypeName" />
            </xsl:call-template>
        </xsl:when>
        <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
                <!-- If List, end the List bracket-->
        <xsl:if test="IsList = 'true'">
        <xsl:text>]</xsl:text>
        </xsl:if>

        <!-- If Optional, end the Optional bracket-->
        <xsl:if test="not(IsRequired = 'true')">
        <xsl:text>]</xsl:text>
        </xsl:if>
    </xsl:variable>

    <xsl:variable name = "attribute-name">
        <xsl:value-of select="Value"/>
        <!-- If attribute is associated to a data class, add Id to the Attribute name-->
        <xsl:if test="not(normalize-space(SubTypeDataClass) = '')">
        <xsl:text>Id</xsl:text>
        </xsl:if>
    </xsl:variable>

    <xsl:if test="
    (IsList='true' and PrimitiveType != '' and normalize-space(Format) != '') or 
    (normalize-space(PrimitiveFormat) != '') or 
    (Axiom != '') or 
    (normalize-space(SubTypeDataClass) != '' and not(IsList='true'))">

    <xsl:text>

    @validator("</xsl:text><xsl:value-of select="$attribute-name"/><xsl:text>"</xsl:text>

    <xsl:if test="PreValidateFormat='true'">
    <xsl:text>, pre=True</xsl:text>
    </xsl:if>
    <xsl:text>)
    def </xsl:text>

    <!-- add an underscore if there are no axioms getting checked, in which case its just property formats and/or enums -->
    <xsl:if test="count($airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)]) = 0">
    <xsl:text>_</xsl:text>
    </xsl:if>

    <xsl:text>check_</xsl:text><xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="$attribute-name"  />
        </xsl:call-template><xsl:text>(cls, v: </xsl:text>
        <xsl:value-of select="$attribute-type"/>
        <xsl:text>) -> </xsl:text>
        <xsl:value-of select="$attribute-type"/>
        <xsl:text>:</xsl:text>

        <xsl:if test="count($airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)]) > 1">
        <xsl:text>
        """
        Axioms </xsl:text>
        <xsl:for-each select="$airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)]">
        <xsl:sort select="AxiomNumber" data-type="number"/>
        <xsl:value-of select="AxiomNumber"/>
                <xsl:if test="position() != count($airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)])">
                <xsl:text>, </xsl:text>
                </xsl:if>
        </xsl:for-each>
        <xsl:text>:</xsl:text>
        </xsl:if>

        <xsl:if test="count($airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)]) = 1">
        <xsl:text>
        """</xsl:text>
        </xsl:if>

        <xsl:if test="count($airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)]) > 0">
        <xsl:for-each select="$airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)]">
        <xsl:sort select="AxiomNumber" data-type="number"/>

        <xsl:if test="count($airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)]) =1">
        <xsl:text>
        Axiom </xsl:text>
        </xsl:if>

        <xsl:if test="count($airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)]) >1">
        <xsl:text>

        Axiom </xsl:text>
        </xsl:if>

        <xsl:value-of select="AxiomNumber"/><xsl:text>: </xsl:text>
        <xsl:value-of select="Title"/>

        <xsl:if test="normalize-space(Description)!=''">
        <xsl:text>.
        </xsl:text>
         <xsl:call-template name="wrap-text">
        <xsl:with-param name="text" select="normalize-space(Description)"/>
        </xsl:call-template>
        </xsl:if>
        <xsl:if test="normalize-space(Url)!=''">
        <xsl:text>
        [More info](</xsl:text><xsl:value-of select="Url"/>
        <xsl:text>)</xsl:text>

        </xsl:if>

        </xsl:for-each>
        <xsl:text>
        """</xsl:text>
        </xsl:if>



        <xsl:if test="not(IsRequired = 'true')">
                <xsl:text>
        if v is None:
            return v</xsl:text>
        </xsl:if>

        <xsl:if test="count($airtable//TypeAxioms/TypeAxiom[(normalize-space(SinglePropertyAxiom)=$type-attribute-id)]) > 0">
        <xsl:text>
        ...
        # TODO: Implement Axiom(s)</xsl:text>
        </xsl:if>

        <xsl:choose>

        <!-- Format needs validating; not a list-->
        <xsl:when test="normalize-space(PrimitiveFormat) !='' and not(IsList='true')">
        <xsl:text>
        try:
            check_is_</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="translate(PrimitiveFormat,'.','_')"  />
                </xsl:call-template>
        <xsl:text>(v)
        except ValueError as e:</xsl:text>
        <xsl:choose>
            <xsl:when test="string-length(PrimitiveFormat) + string-length(Value)> 24">
            <xsl:text>
            raise ValueError(
                f"</xsl:text><xsl:value-of select="Value"/><xsl:text> failed </xsl:text>
            <xsl:value-of select="PrimitiveFormat"/>
            <xsl:text> format validation: {e}"
            )</xsl:text>
            </xsl:when>
            <xsl:otherwise>
            <xsl:text>
            raise ValueError(f"</xsl:text><xsl:value-of select="Value"/><xsl:text> failed </xsl:text>
            <xsl:value-of select="PrimitiveFormat"/>
            <xsl:text> format validation: {e}")</xsl:text>
            </xsl:otherwise>
        </xsl:choose>
        <xsl:text>
        return v</xsl:text>
        </xsl:when>

        <!-- Format needs validating; is a list-->
        <xsl:when test="normalize-space(PrimitiveFormat) !='' and (IsList='true')">
        <xsl:text>
        for elt in v:
            try:
                check_is_</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="translate(PrimitiveFormat,'.','_')"  />
            </xsl:call-template>
        <xsl:text>(elt)
            except ValueError as e:
                raise ValueError(
                    f"</xsl:text><xsl:value-of select="Value"/><xsl:text> element {elt} failed </xsl:text>
                <xsl:value-of select="PrimitiveFormat" />
                <xsl:text> format validation: {e}"
                )
        return v</xsl:text>
        </xsl:when>

         <!-- SubType w Data Class; not a list-->
        <xsl:when test = "not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
        <xsl:text>
        try:
            check_is_uuid_canonical_textual(v)
        except ValueError as e:
            raise ValueError(
                f"</xsl:text>
                <xsl:value-of select="Value"/><xsl:text>Id failed UuidCanonicalTextual format validation: {e}"
            )
        return v</xsl:text>
        </xsl:when>

         <!-- SubType w Data Class; is a list-->
        <xsl:when test="not(normalize-space(SubTypeDataClass) = '') and IsList='true'">
        <xsl:text>
        for elt in v:
            try:
                check_is_uuid_canonical_textual(elt)
            except ValueError as e:
                raise ValueError(
                    f"</xsl:text><xsl:value-of select="Value"/><xsl:text> element {elt} failed </xsl:text>
                <xsl:value-of select="PrimitiveFormat" />
                <xsl:text> format validation: {e}"
                )
        return v</xsl:text>
        </xsl:when>

        <xsl:otherwise>
        </xsl:otherwise>
        </xsl:choose>
    </xsl:if>

        </xsl:for-each>


    <xsl:if test="count($airtable//TypeAxioms/TypeAxiom[MultiPropertyAxiom=$versioned-type-id]) > 0">
    <xsl:for-each select="$airtable//TypeAxioms/TypeAxiom[MultiPropertyAxiom=$versioned-type-id]">
    <xsl:sort select="AxiomNumber" data-type="number"/>
    <xsl:text>

    @root_validator</xsl:text>
    <xsl:if test="CheckFirst='true'">
     <xsl:text>(pre=True)</xsl:text>
    </xsl:if>
    <xsl:text>
    def check_axiom_</xsl:text><xsl:value-of select="AxiomNumber"/><xsl:text>(cls, v: dict) -> dict:
        """
        Axiom </xsl:text><xsl:value-of select="AxiomNumber"/><xsl:text>: </xsl:text>
        <xsl:value-of select="Title"/>
        <xsl:text>.
        </xsl:text><xsl:value-of select="Description"/>
        <xsl:if test="normalize-space(Url)!=''">
        <xsl:text>
        [More info](</xsl:text>
        <xsl:value-of select="normalize-space(Url)"/>
        <xsl:text>)</xsl:text>
        </xsl:if>

        <xsl:text>
        """
        # TODO: Implement check for axiom </xsl:text><xsl:value-of select="AxiomNumber"/><xsl:text>"
        return v</xsl:text>

    </xsl:for-each>
    </xsl:if>


    <!-- DONE WITH VALIDATORS  -->
    <!-- DONE WITH VALIDATORS  -->



    <!-- AS_DICT ######################################################################-->
    <!-- AS_DICT ######################################################################-->
    <!-- AS_DICT ######################################################################-->
    <!-- AS_DICT ######################################################################-->
    <xsl:text>

    def as_dict(self) -> Dict[str, Any]:
        """
        Translate the object into a dictionary representation that can be serialized into a
        </xsl:text><xsl:value-of select="VersionedTypeName"/><xsl:text> object.

        This method prepares the object for serialization by the as_type method, creating a
        dictionary with key-value pairs that follow the requirements for an instance of the
        </xsl:text>
        <xsl:value-of select="VersionedTypeName"/><xsl:text> type. Unlike the standard python dict method,
        it makes the following substantive changes:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.
        """
        d = {
            key: value
            for key, value in self.dict(
                include=self.__fields_set__ | {"TypeName", "Version"}
            ).items()
            if value is not None
        }</xsl:text>

        <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
        <xsl:sort select="Idx" data-type="number"/>

        <xsl:variable name="enum-local-name">
            <xsl:call-template name="nt-case">
                <xsl:with-param name="type-name-text" select="EnumLocalName" />
            </xsl:call-template>
        </xsl:variable>
        <xsl:variable name="enum-class-name">
            <xsl:if test="(normalize-space(UseEnumAlias) = 'true')">
                <xsl:text>Enum</xsl:text>
            </xsl:if>
                <xsl:value-of select="$enum-local-name"/>
        </xsl:variable>

    <xsl:choose>

    <!-- (Required) CASES FOR as_dict -->
    <xsl:when test="IsRequired = 'true'">
    <xsl:choose>

        <!-- (required) as_dict: Single Enums -->
        <xsl:when test="(IsEnum = 'true') and not (IsList = 'true')">
    <xsl:text>
        del d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]
        d["</xsl:text>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="type-name-text" select="Value" />
        </xsl:call-template>
        <xsl:text>GtEnumSymbol"] = </xsl:text><xsl:value-of select="$enum-class-name"/>
        <xsl:text>.value_to_symbol(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>)</xsl:text>
        </xsl:when>

         <!-- (required) as_dict: List of Enums -->
        <xsl:when test="(IsEnum = 'true')  and (IsList = 'true')">
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
        <xsl:value-of select="$enum-local-name"/><xsl:text>.value_to_symbol(elt.value))
        d["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
            <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        </xsl:when>

        <!--(required) as_dict: Single Type, no associated data class (since those just show up as id pointers) -->
        <xsl:when test="(IsType = 'true') and (normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
        <xsl:text>
        d["</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>"] = self.</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>.as_dict()</xsl:text>
        </xsl:when>


        <!-- (required) as_dict: List of Types -->
        <xsl:when test="(IsType = 'true') and (normalize-space(SubTypeDataClass) = '' or IsList='true') and (IsList = 'true')">
        <xsl:text>
        # Recursively calling as_dict()
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
        <xsl:text>.append(elt.as_dict())
        d["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        </xsl:when>
        <xsl:otherwise></xsl:otherwise>
    </xsl:choose>
    </xsl:when>

    <!-- Optional as_dict -->
    <xsl:otherwise>
        <xsl:choose>

        <!-- (optional) as_dict: Single Enums -->
        <xsl:when test="(IsEnum = 'true') and not (IsList = 'true')">
    <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>" in d.keys():
            del d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]
            d["</xsl:text>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="type-name-text" select="Value" />
        </xsl:call-template>
        <xsl:text>GtEnumSymbol"] = </xsl:text><xsl:value-of select="$enum-class-name"/>
        <xsl:text>.value_to_symbol(self.</xsl:text><xsl:value-of select="Value"/><xsl:text>)</xsl:text>
        </xsl:when>

         <!-- (optional) as_dict: List of Enums -->
        <xsl:when test="(IsEnum = 'true')  and (IsList = 'true')">
        <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>" in d.keys():
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
        <xsl:value-of select="$enum-local-name"/><xsl:text>.value_to_symbol(elt.value))
            d["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
            <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        </xsl:when>

        <!--(optional) as_dict: Single Type, no associated data class (since those just show up as id pointers) -->
        <xsl:when test="(IsType = 'true') and (normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
        <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>" in d.keys():
            del d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]
            d["</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>"] = self.</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>.as_dict()</xsl:text>
        </xsl:when>

        <!-- (optional) as_dict: List of Types -->
        <xsl:when test="(IsType = 'true') and (normalize-space(SubTypeDataClass) = '') and (IsList = 'true')">
        <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>" in d.keys():
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
        <xsl:text>.append(elt.as_dict())
            d["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        </xsl:when>
         <!-- End of loop inside optional -->
        <xsl:otherwise></xsl:otherwise>
        </xsl:choose>


    </xsl:otherwise>
    </xsl:choose>

    </xsl:for-each>
    <xsl:text>
        return d

    def as_type(self) -> bytes:
        """
        Serialize to the </xsl:text>
        <xsl:value-of select="VersionedTypeName"/><xsl:text> representation.

        Instances in the class are python-native representations of </xsl:text><xsl:value-of select="VersionedTypeName"/><xsl:text>
        objects, while the actual </xsl:text><xsl:value-of select="VersionedTypeName"/><xsl:text> object is the serialized UTF-8 byte
        string designed for sending in a message.

        This method calls the as_dict() method, which differs from the native python dict()
        in the following key ways:
        - Enum Values: Translates between the values used locally by the actor to the symbol
        sent in messages.
        - - Removes any key-value pairs where the value is None for a clearer message, especially
        in cases with many optional attributes.

        It also applies these changes recursively to sub-types.

        Its near-inverse is </xsl:text>
        <xsl:value-of select="$python-class-name"/>
        <xsl:text>.type_to_tuple(). If the type (or any sub-types)
        includes an enum, then the type_to_tuple will map an unrecognized symbol to the
        default enum value. This is why these two methods are only 'near' inverses.
        """
        json_string = json.dumps(self.as_dict())
        return json_string.encode("utf-8")

    def __hash__(self):
        return hash((type(self),) + tuple(self.__dict__.values()))  # noqa


class </xsl:text>
    <xsl:value-of select="$python-class-name"/>
    <xsl:text>_Maker:
    type_name = "</xsl:text><xsl:value-of select="TypeName"/><xsl:text>"
    version = "</xsl:text><xsl:value-of select="Version"/><xsl:text>"

    def __init__(
        self,
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

<xsl:variable name="enum-class-name">
    <xsl:if test = "(IsEnum = 'true')">
        <xsl:if test="UseEnumAlias = 'true'">
        <xsl:text>Enum</xsl:text>
        </xsl:if>
        <xsl:call-template name="nt-case">
                        <xsl:with-param name="type-name-text" select="EnumLocalName" />
        </xsl:call-template>
    </xsl:if>
</xsl:variable>

<xsl:variable name="attribute-type">

    <!-- If Optional, start the Optional bracket-->
    <xsl:if test="not(IsRequired = 'true')">
    <xsl:text>Optional[</xsl:text>
    </xsl:if>

    <!-- If List, start the List bracket-->
    <xsl:if test="IsList = 'true'">
    <xsl:text>List[</xsl:text>
    </xsl:if>
    <xsl:choose>
    <xsl:when test="(IsPrimitive = 'true')">
    <xsl:call-template name="python-type">
        <xsl:with-param name="gw-type" select="PrimitiveType"/>
    </xsl:call-template>
    </xsl:when>

    <xsl:when test = "(IsEnum = 'true')">
        <xsl:value-of select="$enum-class-name"/>
    </xsl:when>

    <!-- If Attribute is a type associated with a dataclass, the reference is to its id, which is a string -->
    <xsl:when test = "not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
    <xsl:text>str</xsl:text>
    </xsl:when>

    <!-- Otherwise, the reference is to the type  -->
    <xsl:when test="(IsType = 'true')">
        <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="SubTypeName" />
        </xsl:call-template>
    </xsl:when>
    <xsl:otherwise></xsl:otherwise>
    </xsl:choose>
            <!-- If List, end the List bracket-->
    <xsl:if test="IsList = 'true'">
    <xsl:text>]</xsl:text>
    </xsl:if>

    <!-- If Optional, end the Optional bracket-->
    <xsl:if test="not(IsRequired = 'true')">
    <xsl:text>]</xsl:text>
    </xsl:if>
</xsl:variable>


        <!-- python case version of attribute names in init-->
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="$attribute-name"  />
        </xsl:call-template>
        <xsl:text>: </xsl:text>
        <xsl:value-of select="$attribute-type"/>

        <xsl:variable name="current-attribute" select="position()" />
        <xsl:choose>
        <xsl:when test="$current-attribute=$total-attributes">
        <xsl:text>,</xsl:text>
        </xsl:when>
        <xsl:otherwise>
        <xsl:text>,
        </xsl:text>
        </xsl:otherwise>
        </xsl:choose>


        </xsl:for-each>
    <xsl:text>
    ):
        self.tuple = </xsl:text><xsl:value-of select="$python-class-name"/>
        <xsl:text>(
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

        <xsl:value-of select="$attribute-name"/><xsl:text>=</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="$attribute-name"  />
        </xsl:call-template>

        <xsl:variable name="current-attribute" select="position()" />
        <xsl:choose>
        <xsl:when test="$current-attribute=$total-attributes">
        <xsl:text>,</xsl:text>
        </xsl:when>
        <xsl:otherwise>
        <xsl:text>,
            </xsl:text>
        </xsl:otherwise>
        </xsl:choose>

    </xsl:for-each>
    <xsl:text>
        )

    @classmethod
    def tuple_to_type(cls, tuple: </xsl:text><xsl:value-of select="$python-class-name"/>
    <xsl:text>) -> bytes:
        """
        Given a Python class object, returns the serialized JSON type object.
        """
        return tuple.as_type()

    @classmethod
    def type_to_tuple(cls, t: bytes) -> </xsl:text><xsl:value-of select="$python-class-name"/>
<xsl:text>:
        """
        Given a serialized JSON type object, returns the Python class object.
        """
        try:
            d = json.loads(t)
        except TypeError:
            raise SchemaError("Type must be string or bytes!")
        if not isinstance(d, dict):
            raise SchemaError(f"Deserializing &lt;{t}> must result in dict!")
        return cls.dict_to_tuple(d)

    @classmethod
    def dict_to_tuple(cls, d: dict[str, Any]) -> </xsl:text><xsl:value-of select="$python-class-name"/>
    <xsl:text>:
        """
        Deserialize a dictionary representation of a </xsl:text><xsl:value-of select="VersionedTypeName"/>
        <xsl:text> message object
        into a </xsl:text>
        <xsl:value-of select="$python-class-name"/><xsl:text> python object for internal use.

        This is the near-inverse of the </xsl:text><xsl:value-of select="$python-class-name"/>
        <xsl:text>.as_dict() method:
          - Enums: translates between the symbols sent in messages between actors and
        the values used by the actors internally once they've deserialized the messages.
          - Types: recursively validates and deserializes sub-types.

        Note that if a required attribute with a default value is missing in a dict, this method will
        raise a SchemaError. This differs from the pydantic BaseModel practice of auto-completing
        missing attributes with default values when they exist.

        Args:
            d (dict): the dictionary resulting from json.loads(t) for a serialized JSON type object t.

        Raises:
           SchemaError: if the dict cannot be turned into a </xsl:text><xsl:value-of select="$python-class-name"/><xsl:text> object.

        Returns:
            </xsl:text><xsl:value-of select="$python-class-name"/><xsl:text>
        """
        d2 = dict(d)</xsl:text>

<xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
<xsl:sort select="Idx" data-type="number"/>
<xsl:variable name="enum-local-name">
    <xsl:call-template name="nt-case">
        <xsl:with-param name="type-name-text" select="EnumLocalName" />
    </xsl:call-template>
</xsl:variable>
<xsl:variable name="enum-class-name">
    <xsl:if test="(normalize-space(UseEnumAlias) = 'true')">
        <xsl:text>Enum</xsl:text>
    </xsl:if>
        <xsl:value-of select="$enum-local-name"/>
</xsl:variable>

    <xsl:choose>

    <!-- Check for enum or type -->
    <xsl:when test="(IsEnum = 'true') or (IsType = 'true' and (normalize-space(SubTypeDataClass) = '' or IsList='true'))">
    <!-- OUTER LOOP dict_to_tuple -->
    <xsl:choose>

     <!-- OUTER LOOP dict_to_tuple: attribute is required-->
    <xsl:when test= "IsRequired='true'">
        <!-- INNER LOOP dict_to_tuple -->
        <xsl:choose>
            <!-- (Is required) INNER LOOP dict_to_tuple: Single Enum -->
        <xsl:when test="(IsEnum = 'true') and not (IsList = 'true')">
        <xsl:text>
        if "</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="Value" />
        </xsl:call-template><xsl:text>GtEnumSymbol" not in d2.keys():
            raise SchemaError(f"</xsl:text>
            <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="Value" />
        </xsl:call-template>
            <xsl:text>GtEnumSymbol missing from dict &lt;{d2}>")
        value = </xsl:text>
        <xsl:value-of select="$enum-class-name"/>
        <xsl:text>.symbol_to_value(d2["</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="Value" />
        </xsl:call-template><xsl:text>GtEnumSymbol"])
        d2["</xsl:text> <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="Value" />
        </xsl:call-template><xsl:text>"] = </xsl:text>
        <xsl:value-of select="$enum-class-name"/>
        <xsl:text>(value)
        del d2["</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="Value" />
        </xsl:call-template><xsl:text>GtEnumSymbol"]</xsl:text>
        </xsl:when>

        <!-- (Is required) INNER LOOP dict_to_tuple:  Enum List -->
        <xsl:when test="(IsEnum = 'true') and (IsList = 'true')">
        <xsl:text>
        if "</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>" not in d2.keys():
            raise SchemaError(f"dict &lt;{d2}> missing </xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>")
        if not isinstance(d2["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"], List):
            raise SchemaError("</xsl:text><xsl:value-of select="Value"/><xsl:text> must be a List!")
        </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text> = []
        for elt in d2["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"]:
            value = </xsl:text>
            <xsl:value-of select="$enum-class-name"/>
            <xsl:text>.symbol_to_value(elt)
            </xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
            <xsl:text>.append(</xsl:text>
            <xsl:value-of select="$enum-class-name"/><xsl:text>(value))
        d2["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        </xsl:when>

         <!-- (Is required) INNER LOOP dict_to_tuple: Single type not Dataclass -->
        <xsl:when test="(IsType = 'true') and (normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
        <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" not in d2.keys():
            raise SchemaError(f"dict missing </xsl:text><xsl:value-of select="Value"/><xsl:text>: &lt;{d2}>")
        if not isinstance(d2["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"], dict):
            raise SchemaError(f"</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text> &lt;{d2['</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>']}> must be a </xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="type-name-text" select="SubTypeName" />
            </xsl:call-template>
            <xsl:text>!")
        </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text> = </xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="SubTypeName" />
        </xsl:call-template>
        <xsl:text>_Maker.dict_to_tuple(d2["</xsl:text>
        <xsl:value-of select="Value"/>
        <xsl:text>"])
        d2["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        </xsl:when>

        <!-- (Is required) INNER LOOP dict_to_tuple: List of types (can be data class) -->
        <xsl:when test="(IsType = 'true') and (IsList = 'true')">
        <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" not in d2.keys():
            raise SchemaError(f"dict missing </xsl:text><xsl:value-of select="Value"/><xsl:text>: &lt;{d2}>")
        if not isinstance(d2["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"], List):
            raise SchemaError(f"</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text> &lt;{d2['</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>']}> must be a List!")
        </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text> = []
        for elt in d2["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"]:
            if not isinstance(elt, dict):
                raise SchemaError(f"</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text> &lt;{d2['</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>']}> must be a List of </xsl:text>
            <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="SubTypeName" />
            </xsl:call-template>
            <xsl:text> types")
            t = </xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="type-name-text" select="SubTypeName" />
        </xsl:call-template>
        <xsl:text>_Maker.dict_to_tuple(elt)
            </xsl:text><xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>.append(t)
        d2["</xsl:text><xsl:value-of select="Value"/>
        <xsl:text>"] = </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        </xsl:when>

        <!-- Completing REQUIRED inner loop choose-->
        <xsl:otherwise></xsl:otherwise>
        </xsl:choose>
    </xsl:when>

     <!-- OUTER LOOP dict_to_tuple: attribute is optional-->
    <xsl:otherwise>
    <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" in d2.keys():
            </xsl:text>

        <xsl:choose>

        <!-- (Is required) INNER LOOP dict_to_tuple: Single Enum -->
            <xsl:when test="(IsEnum = 'true') and not (IsList = 'true')">
            <xsl:text>value = </xsl:text>
            <xsl:value-of select="$enum-class-name"/>
            <xsl:text>.symbol_to_value(d2["</xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="type-name-text" select="Value" />
            </xsl:call-template><xsl:text>GtEnumSymbol"])
            d2["</xsl:text> <xsl:call-template name="nt-case">
                <xsl:with-param name="type-name-text" select="Value" />
            </xsl:call-template><xsl:text>"] = </xsl:text>
            <xsl:value-of select="$enum-class-name"/>
            <xsl:text>(value)</xsl:text>
            </xsl:when>
            <!-- (Is optional) INNER LOOP dict_to_tuple: Single type not Dataclass -->
            <xsl:when test="(IsType = 'true') and (normalize-space(SubTypeDataClass) = '') and not (IsList = 'true')">
            <xsl:text>if not isinstance(d2["</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>"], dict):
                raise SchemaError(f"d['</xsl:text>
                <xsl:value-of select="Value"/>
                <xsl:text>'] &lt;{d2['</xsl:text><xsl:value-of select="Value"/>
                <xsl:text>']}> must be a </xsl:text>
                <xsl:call-template name="nt-case">
                    <xsl:with-param name="type-name-text" select="SubTypeName" />
                </xsl:call-template>
                <xsl:text>!")
            </xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
            <xsl:text> = </xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="type-name-text" select="SubTypeName" />
            </xsl:call-template>
            <xsl:text>_Maker.dict_to_tuple(d2["</xsl:text>
            <xsl:value-of select="Value"/>
            <xsl:text>"])
            d2["</xsl:text><xsl:value-of select="Value"/>
            <xsl:text>"] = </xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
            </xsl:when>

         <!-- Completing OPTIONAL inner loop choose-->
        <xsl:otherwise></xsl:otherwise>
        </xsl:choose>

    </xsl:otherwise>
    </xsl:choose>

    <!-- Finishing clause testing for enum or type -->
    </xsl:when>
    <xsl:otherwise>
    <xsl:if test="IsRequired='true'">
    <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/>

        <xsl:if test="not(normalize-space(SubTypeDataClass) = '') and not(IsList='true')">
        <xsl:text>Id</xsl:text>
        </xsl:if>


        <xsl:text>" not in d2.keys():
            raise SchemaError(f"dict missing </xsl:text><xsl:value-of select="Value"/><xsl:text>: &lt;{d2}>")</xsl:text>

    </xsl:if>

    </xsl:otherwise>
    </xsl:choose>
<!-- finishing for-each for dict_to_tuple attributes-->
</xsl:for-each>


<xsl:text>
        if "TypeName" not in d2.keys():
            raise SchemaError(f"TypeName missing from dict &lt;{d2}>")
        if "Version" not in d2.keys():
            raise SchemaError(f"Version missing from dict &lt;{d2}>")
        if d2["Version"] != "</xsl:text><xsl:value-of select="Version"/><xsl:text>":
            LOGGER.debug(
                f"Attempting to interpret </xsl:text>
            <xsl:value-of select="TypeName"/>
            <xsl:text> version {d2['Version']} as version </xsl:text>
            <xsl:value-of select="Version"/> <xsl:text>"
            )
            d2["Version"] = "</xsl:text><xsl:value-of select="Version"/><xsl:text>"
        return </xsl:text><xsl:value-of select="$python-class-name"/><xsl:text>(**d2)</xsl:text>
    <xsl:if test="(MakeDataClass='true')">
    <xsl:text>

    @classmethod
    def tuple_to_dc(cls, t: </xsl:text><xsl:value-of select="$python-class-name"/>
    <xsl:text>) -> </xsl:text><xsl:value-of select="DataClass"/><xsl:text>:
        if t.</xsl:text><xsl:value-of select="DataClassIdField"/><xsl:text> in </xsl:text>
        <xsl:value-of select="DataClass"/><xsl:text>.by_id.keys():
            dc = </xsl:text><xsl:value-of select="DataClass"/><xsl:text>.by_id[t.</xsl:text>
            <xsl:value-of select="DataClassIdField"/><xsl:text>]
        else:
            dc = </xsl:text><xsl:value-of select="DataClass"/><xsl:text>(
                </xsl:text>
        <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
        <xsl:sort select="Idx" data-type="number"/>
        <xsl:choose>

        <!-- Single type associated with a single dataclass -->
        <xsl:when test="not(normalize-space(SubTypeDataClass) = '') and not(IsList = 'true')">
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>_id=t.</xsl:text>
            <xsl:value-of select="Value"/><xsl:text>Id</xsl:text>
        </xsl:when>
        <!-- For all other classes -->
        <xsl:otherwise>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text>=t.</xsl:text>
            <xsl:value-of select="Value"/>
        </xsl:otherwise>

        </xsl:choose>
                <xsl:variable name="current-attribute" select="position()" />
                <xsl:choose>
                <xsl:when test="$current-attribute=$total-attributes">
                <xsl:text>,</xsl:text>
                </xsl:when>
                <xsl:otherwise>
                <xsl:text>,
                </xsl:text>
                </xsl:otherwise>
                </xsl:choose>


    </xsl:for-each>
            <xsl:text>
            )
        return dc

    @classmethod
    def dc_to_tuple(cls, dc: </xsl:text><xsl:value-of select="DataClass"/><xsl:text>) -> </xsl:text><xsl:value-of select="$python-class-name"/><xsl:text>:
        t = </xsl:text><xsl:value-of select="$python-class-name"/><xsl:text>_Maker(
            </xsl:text>
        <xsl:for-each select="$airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id)]">
        <xsl:sort select="Idx" data-type="number"/>
        <xsl:choose>
        <!-- Single type associated with a single dataclass -->
        <xsl:when test="not(normalize-space(SubTypeDataClass) = '') and not(IsList = 'true')">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>_id=dc.</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
        <xsl:text>_id,
            </xsl:text>
        </xsl:when>

         <!-- For all other classes -->
        <xsl:otherwise>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>=dc.</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>


            <xsl:variable name="current-attribute" select="position()" />
            <xsl:choose>
            <xsl:when test="$current-attribute=$total-attributes">
            <xsl:text>,</xsl:text>
            </xsl:when>
            <xsl:otherwise>
            <xsl:text>,
            </xsl:text>
            </xsl:otherwise>
            </xsl:choose>


        </xsl:otherwise>
        </xsl:choose>


        </xsl:for-each>
        <xsl:text>
        ).tuple
        return t

    @classmethod
    def type_to_dc(cls, t: str) -> </xsl:text><xsl:value-of select="DataClass"/><xsl:text>:
        return cls.tuple_to_dc(cls.type_to_tuple(t))

    @classmethod
    def dc_to_type(cls, dc: </xsl:text><xsl:value-of select="DataClass"/><xsl:text>) -> str:
        return cls.dc_to_tuple(dc).as_type()

    @classmethod
    def dict_to_dc(cls, d: dict[Any, str]) -> </xsl:text><xsl:value-of select="DataClass"/><xsl:text>:
        return cls.tuple_to_dc(cls.dict_to_tuple(d))</xsl:text>
</xsl:if>


<xsl:for-each select="$airtable//GtEnums/GtEnum[(normalize-space(Name) !='')  and (count(TypesThatUse[text()=$versioned-type-id])>0)]">
<xsl:variable name="enum-name-style" select="PythonEnumNameStyle" />
<xsl:variable name="local-name" select="LocalName"/>
<xsl:variable name="enum-local-name">
    <xsl:call-template name="nt-case">
        <xsl:with-param name="type-name-text" select="LocalName" />
    </xsl:call-template>
</xsl:variable>
<xsl:variable name="enum-class-name">
    <xsl:if test="count($airtable//TypeAttributes/TypeAttribute[(VersionedType = $versioned-type-id) and (UseEnumAlias ='true') and (EnumLocalName[text() = $local-name])])>0">
        <xsl:text>Enum</xsl:text>
    </xsl:if>
        <xsl:value-of select="$enum-local-name"/>
</xsl:variable>
<xsl:variable name="enum-id" select="GtEnumId"/>
<xsl:variable name="enum-version" select="Version"/>




</xsl:for-each>

<xsl:if test="count(PropertyFormatsUsed)>0">
<xsl:for-each select="$airtable//PropertyFormats/PropertyFormat[(normalize-space(Name) !='')  and (count(TypesThatUse[text()=$versioned-type-id])>0)]">
<xsl:sort select="Name" data-type="text"/>
<xsl:choose>
    <xsl:when test="Name='AlgoAddressStringFormat'">
    <xsl:text>


def check_is_algo_address_string_format(v: str) -> None:
    """
    AlgoAddressStringFormat format: The public key of a private/public Ed25519
    key pair, transformed into an  Algorand address, by adding a 4-byte checksum
    to the end of the public key and then encoding in base32.

    Raises:
        ValueError: if not AlgoAddressStringFormat format
    """
    import algosdk
    at = algosdk.abi.AddressType()
    try:
        result = at.decode(at.encode(v))
    except Exception as e:
        raise ValueError(f"Not AlgoAddressStringFormat: {e}")</xsl:text>
    </xsl:when>


    <xsl:when test="Name='AlgoMsgPackEncoded'">
    <xsl:text>


def check_is_algo_msg_pack_encoded(v: str) -> None:
    """
    AlgoMSgPackEncoded format: the format of a transaction sent to
    the Algorand blockchain. Error is not thrown with
    algosdk.encoding.future_msg_decode(candidate)

    Raises:
        ValueError: if not AlgoMSgPackEncoded  format
    """
    import algosdk
    try:
        algosdk.encoding.future_msgpack_decode(v)
    except Exception as e:
        raise ValueError(f"Not AlgoMsgPackEncoded format: {e}")</xsl:text>
    </xsl:when>

    <xsl:when test="Name='Bit'">
    <xsl:text>


def check_is_bit(v: int) -> None:
    """
    Checks Bit format

    Bit format: The value must be the integer 0 or the integer 1.

    Will not attempt to first interpret as an integer. For example,
    1.3 will not be interpreted as 1 but will raise an error.

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not 0 or 1
    """
    if not v in [0,1]:
        raise ValueError(f"&lt;{v}> must be 0 or 1")</xsl:text>

    </xsl:when>

    <xsl:when test="Name='HexChar'">
    <xsl:text>


def check_is_hex_char(v: str) -> None:
    """Checks HexChar format

    HexChar format: single-char string in '0123456789abcdefABCDEF'

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not HexChar format
    """
    if not isinstance(v, str):
        raise ValueError(f"&lt;{v}> must be a hex char, but not even a string")
    if len(v) > 1:
        raise ValueError(f"&lt;{v}> must be a hex char, but not of len 1")
    if v not in "0123456789abcdefABCDEF":
        raise ValueError(f"&lt;{v}> must be one of '0123456789abcdefABCDEF'")</xsl:text>
    </xsl:when>


    <xsl:when test="Name='IsoFormat'">
    <xsl:text>


def check_is_iso_format(v: str) -> None:
    """
    Example: '2024-01-10T15:30:45.123456-05:00'  The string does not
    need to include microseconds.
    """
    import datetime

    try:
        datetime.datetime.fromisoformat(v.replace("Z", "+00:00"))
    except:
        raise ValueError(f"&lt;{v}> is not IsoFormat")</xsl:text>
    </xsl:when>


    <xsl:when test="Name='LeftRightDot'">
    <xsl:text>


def check_is_left_right_dot(v: str) -> None:
    """Checks LeftRightDot Format

    LeftRightDot format: Lowercase alphanumeric words separated by periods, with
    the most significant word (on the left) starting with an alphabet character.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LeftRightDot format
    """
    from typing import List

    try:
        x: List[str] = v.split(".")
    except:
        raise ValueError(f"Failed to seperate &lt;{v}> into words with split'.'")
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"Most significant word of &lt;{v}> must start with alphabet char."
        )
    for word in x:
        if not word.isalnum():
            raise ValueError(f"words of &lt;{v}> split by by '.' must be alphanumeric.")
    if not v.islower():
        raise ValueError(f"All characters of &lt;{v}> must be lowercase.")</xsl:text>

    </xsl:when>

    <xsl:when test="Name='LogStyleDateWithMillis'">
    <xsl:text>


def check_is_log_style_date_with_millis(v: str) -> None:
    """Checks LogStyleDateWithMillis format

    LogStyleDateWithMillis format:  YYYY-MM-DDTHH:mm:ss.SSS

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not LogStyleDateWithMillis format. 
        In particular the milliseconds must have exactly 3 digits.
    """
    from datetime import datetime
    try:
        datetime.fromisoformat(v)
    except ValueError:
        raise ValueError(f"{v} is not in LogStyleDateWithMillis format")
    # The python fromisoformat allows for either 3 digits (milli) or 6 (micro)
    # after the final period. Make sure its 3
    milliseconds_part = v.split(".")[1]
    if len(milliseconds_part) != 3:
        raise ValueError(f"{v} is not in LogStyleDateWithMillis format."
                            " Milliseconds must have exactly 3 digits")    
    </xsl:text>

    </xsl:when>

    <xsl:when test="Name='MarketSlotNameLrdFormat'">
    <xsl:text>


def check_is_market_type_name_lrd_format(v: str) -> None:
    from gwproto.enums import MarketTypeName
    try:
        x = v.split(".")
    except AttributeError:
        raise ValueError(f"&lt;{v}> failed to split on '.'")
    if not x[0] in MarketTypeName.values():
        raise ValueError(f"&lt;{v}> not recognized MarketType")
    g_node_alias = ".".join(x[1:])
    check_is_left_right_dot(g_node_alias)


def check_is_market_slot_name_lrd_format(v: str) -> None:
    """
    MaketSlotNameLrdFormat: the format of a MarketSlotName.
      - The first word must be a MarketTypeName
      - The last word (unix time of market slot start) must
      be a 10-digit integer divisible by 300 (i.e. all MarketSlots
      start at the top of 5 minutes)
      - More strictly, the last word must be the start of a
      MarketSlot for that MarketType (i.e. divisible by 3600
      for hourly markets)
      - The middle words have LeftRightDot format (GNodeAlias
      of the MarketMaker)
    Example: rt60gate5.d1.isone.ver.keene.1673539200

    """
    from gwproto.data_classes.market_type import MarketType
    try:
        x = v.split(".")
    except AttributeError:
        raise ValueError(f"&lt;{v}> failed to split on '.'")
    slot_start = x[-1]
    if len(slot_start) != 10:
        raise ValueError(f"slot start {slot_start} not of length 10")
    try:
        slot_start = int(slot_start)
    except ValueError:
        raise ValueError(f"slot start {slot_start} not an int")
    if slot_start % 300 != 0:
        raise ValueError(f"slot start {slot_start} not a multiple of 300")

    market_type_name_lrd = ".".join(x[:-1])
    try:
        check_is_market_type_name_lrd_format(market_type_name_lrd)
    except ValueError as e:
        raise ValueError(f"e")

    market_type = MarketType.by_id[market_type_name_lrd.split(".")[0]]
    if not slot_start % (market_type.duration_minutes * 60) == 0:
        raise ValueError(
            f"market_slot_start_s mod {(market_type.duration_minutes * 60)} must be 0"
        )</xsl:text>
    </xsl:when>

    <xsl:when test="Name='NonNegativeInteger'">
    <xsl:text>


def check_is_non_negative_integer(v: int) -> None:
    """
    Must be non-negative when interpreted as an integer. Interpretation
    as an integer follows the pydantic rules for this - which will round
    down rational numbers. So 0 is fine, and 1.7 will be interpreted as
    1 and is also fine.

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v &lt; 0
    """
    v2 = int(v)
    if v2 &lt; 0:
        raise ValueError(f"&lt;{v}> is not NonNegativeInteger")</xsl:text>
    </xsl:when>


    <xsl:when test="Name='PositiveInteger'">
    <xsl:text>


def check_is_positive_integer(v: int) -> None:
    """
    Must be positive when interpreted as an integer. Interpretation as an
    integer follows the pydantic rules for this - which will round down
    rational numbers. So 1.7 will be interpreted as 1 and is also fine,
    while 0.5 is interpreted as 0 and will raise an exception.

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v &lt; 1
    """
    v2 = int(v)
    if v2 &lt; 1:
        raise ValueError(f"&lt;{v}> is not PositiveInteger")</xsl:text>
    </xsl:when>

    <xsl:when test="Name='ReasonableUnixTimeMs'">
    <xsl:text>


def check_is_reasonable_unix_time_ms(v: int) -> None:
    """Checks ReasonableUnixTimeMs format

    ReasonableUnixTimeMs format: unix milliseconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeMs format
    """
    import pendulum

    if pendulum.parse("2000-01-01T00:00:00Z").int_timestamp * 1000 > v:  # type: ignore[attr-defined]
        raise ValueError(f"&lt;{v}> must be after Jan 1 2000")
    if pendulum.parse("3000-01-01T00:00:00Z").int_timestamp * 1000 &lt; v:  # type: ignore[attr-defined]
        raise ValueError(f"&lt;{v}> must be before Jan 1 3000")</xsl:text>


    </xsl:when>

    <xsl:when test="Name='ReasonableUnixTimeS'">
    <xsl:text>


def check_is_reasonable_unix_time_s(v: int) -> None:
    """Checks ReasonableUnixTimeS format

    ReasonableUnixTimeS format: unix seconds between Jan 1 2000 and Jan 1 3000

    Args:
        v (int): the candidate

    Raises:
        ValueError: if v is not ReasonableUnixTimeS format
    """
    import pendulum
    if pendulum.parse("2000-01-01T00:00:00Z").int_timestamp > v:  # type: ignore[attr-defined]
        raise ValueError(f"&lt;{v}> must be after Jan 1 2000")
    if pendulum.parse("3000-01-01T00:00:00Z").int_timestamp &lt; v:  # type: ignore[attr-defined]
        raise ValueError(f"&lt;{v}> must be before Jan 1 3000")</xsl:text>

    </xsl:when>


    <xsl:when test="Name='SpaceheatName'">
    <xsl:text>


def check_is_spaceheat_name(v: str) -> None:
    """Check SpaceheatName Format.

    Validates if the provided string adheres to the SpaceheatName format:
    Lowercase words separated by periods, where word characters can be alphanumeric
    or a hyphen, and the first word starts with an alphabet character.

    Args:
        candidate (str): The string to be validated.

    Raises:
        ValueError: If the provided string is not in SpaceheatName format.
    """
    from typing import List
    try:
        x: List[str] = v.split(".")
    except:
        raise ValueError(f"Failed to seperate &lt;{v}> into words with split'.'")
    first_word = x[0]
    first_char = first_word[0]
    if not first_char.isalpha():
        raise ValueError(
            f"Most significant word of &lt;{v}> must start with alphabet char."
        )
    for word in x:
        for char in word:
            if not (char.isalnum() or char == '-'):
                raise ValueError(f"words of &lt;{v}> split by by '.' must be alphanumeric or hyphen.")
    if not v.islower():
        raise ValueError(f"&lt;{v}> must be lowercase.")</xsl:text>
    </xsl:when>

    <xsl:when test="Name='UuidCanonicalTextual'">
    <xsl:text>


def check_is_uuid_canonical_textual(v: str) -> None:
    """Checks UuidCanonicalTextual format

    UuidCanonicalTextual format:  A string of hex words separated by hyphens
    of length 8-4-4-4-12.

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not UuidCanonicalTextual format
    """
    try:
        x = v.split("-")
    except AttributeError as e:
        raise ValueError(f"Failed to split on -: {e}")
    if len(x) != 5:
        raise ValueError(f"&lt;{v}> split by '-' did not have 5 words")
    for hex_word in x:
        try:
            int(hex_word, 16)
        except ValueError:
            raise ValueError(f"Words of &lt;{v}> are not all hex")
    if len(x[0]) != 8:
        raise ValueError(f"&lt;{v}> word lengths not 8-4-4-4-12")
    if len(x[1]) != 4:
        raise ValueError(f"&lt;{v}> word lengths not 8-4-4-4-12")
    if len(x[2]) != 4:
        raise ValueError(f"&lt;{v}> word lengths not 8-4-4-4-12")
    if len(x[3]) != 4:
        raise ValueError(f"&lt;{v}> word lengths not 8-4-4-4-12")
    if len(x[4]) != 12:
        raise ValueError(f"&lt;{v}> word lengths not 8-4-4-4-12")</xsl:text>


    </xsl:when>

    <xsl:when test="Name='WorldInstanceNameFormat'">
    <xsl:text>


def check_is_world_instance_name_format(v: str) -> None:
    """Checks WorldInstanceName Format

    WorldInstanceName format: A single alphanumerical word starting
    with an alphabet char (the root GNodeAlias) and an integer,
    seperated by '__'. For example 'd1__1'

    Args:
        v (str): the candidate

    Raises:
        ValueError: if v is not WorldInstanceNameFormat format
    """
    try:
        words = v.split("__")
    except:
        raise ValueError(f"&lt;{v}> is not split by '__'")
    if len(words) != 2:
        raise ValueError(f"&lt;{v}> not 2 words separated by '__'")
    try:
        int(words[1])
    except:
        raise ValueError(f"&lt;{v}> second word not an int")

    root_g_node_alias = words[0]
    first_char = root_g_node_alias[0]
    if not first_char.isalpha():
        raise ValueError(f"&lt;{v}> first word must be alph char")
    if not root_g_node_alias.isalnum():
        raise ValueError(f"&lt;{v}> first word must be alphanumeric")</xsl:text>
    </xsl:when>
    </xsl:choose>

</xsl:for-each>
</xsl:if>

<!-- Add newline at EOF for git and pre-commit-->
<xsl:text>&#10;</xsl:text>

                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>
                </xsl:for-each>
            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>
