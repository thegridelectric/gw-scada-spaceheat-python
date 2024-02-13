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

            <FileSetFile>
                    <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/gwtypes/__init__.py</xsl:text></xsl:element>

                <OverwriteMode>Always</OverwriteMode>
                <xsl:element name="FileContents">
<xsl:text>
""" List of all the types used by SCADA """

# Types from gwproto</xsl:text>




<xsl:for-each select="$airtable//VersionedTypes/VersionedType[
  count(Protocols[text()='gwproto']) > 0 and 
  (Status = 'Active' or Status = 'Pending') and 
  (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial')
]">
<xsl:sort select="VersionedTypeName" data-type="text"/>
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
<xsl:choose>

<!-- Types that apparently create circular reference issues when added to init in their original repository-->
<xsl:when test="(NotInInit='true')">
<xsl:text>
from gwproto.types.</xsl:text>
<xsl:value-of select="translate(TypeName,'.','_')"/>
<xsl:text>  import </xsl:text>
<xsl:value-of select="$python-class-name"/>
<xsl:text>
from gwproto.types.</xsl:text>
<xsl:value-of select="translate(TypeName,'.','_')"/>
<xsl:text> import </xsl:text><xsl:value-of select="$python-class-name"/>
<xsl:text>_Maker</xsl:text>
</xsl:when>

<!-- Typical types that don't appear to create circular reference issues-->
<xsl:otherwise>

<xsl:text>
from gwproto.types import </xsl:text>
<xsl:value-of select="$python-class-name"/>
<xsl:text>
from gwproto.types import </xsl:text><xsl:value-of select="$python-class-name"/>
<xsl:text>_Maker</xsl:text>

</xsl:otherwise>

</xsl:choose>
</xsl:for-each>

<xsl:text>

# Types from SCADA</xsl:text>

<xsl:for-each select="$airtable//VersionedTypes/VersionedType[
  count(Protocols[text()='scada']) > 0 and 
  (Status = 'Active' or Status = 'Pending') and 
  (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial') and
  not (NotInInit='true')
]">
<xsl:sort select="VersionedTypeName" data-type="text"/>

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

<xsl:text>
from gwtypes.</xsl:text>
<xsl:value-of select="translate(TypeName,'.','_')"/>
<xsl:text> import </xsl:text>
<xsl:value-of select="$python-class-name"/>
<xsl:text>
from gwtypes.</xsl:text>
<xsl:value-of select="translate(TypeName,'.','_')"/>
<xsl:text> import </xsl:text><xsl:value-of select="$python-class-name"/>
<xsl:text>_Maker</xsl:text>
</xsl:for-each>



<xsl:text>


__all__ = [</xsl:text>

<xsl:for-each select="$airtable//VersionedTypes/VersionedType[
  (
    count(Protocols[text()='gwproto']) > 0 or
    count(Protocols[text()='scada']) > 0
  ) and 
  (Status = 'Active' or Status = 'Pending') and 
  (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial')
]">


<xsl:sort select="VersionedTypeName" data-type="text"/>
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

<xsl:choose>
<!-- The type is from scada and not in the init: comment it out-->
<xsl:when test="(NotInInit='true') and count(Protocols[text()='scada']) > 0">
<xsl:text>
    # "</xsl:text>
    <xsl:value-of select="$python-class-name"/>
    <xsl:text>",
    # "</xsl:text>
    <xsl:value-of select="$python-class-name"/>
    <xsl:text>_Maker",</xsl:text>
</xsl:when>

<!-- The type is in the init (including for those types that were not in the gwproto init)-->
<xsl:otherwise>
<xsl:text>
    "</xsl:text>
    <xsl:value-of select="$python-class-name"/>
    <xsl:text>",
    "</xsl:text>
    <xsl:value-of select="$python-class-name"/>
    <xsl:text>_Maker",</xsl:text>
</xsl:otherwise>
</xsl:choose>

</xsl:for-each>

<xsl:text>
]</xsl:text>

<!-- Add newline at EOF for git and pre-commit-->
<xsl:text>&#10;</xsl:text>

                </xsl:element>
            </FileSetFile>


        </FileSet>
    </xsl:template>


</xsl:stylesheet>
