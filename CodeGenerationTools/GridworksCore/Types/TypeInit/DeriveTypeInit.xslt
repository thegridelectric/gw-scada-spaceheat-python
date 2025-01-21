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
                    <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/named_types/__init__.py</xsl:text></xsl:element>

                <OverwriteMode>Always</OverwriteMode>
                <xsl:element name="FileContents">
<xsl:text>""" List of all the types """

from named_types.events import RemainingElecEvent</xsl:text>
<xsl:for-each select="$airtable//VersionedTypes/VersionedType[
  count(Protocols[text()='scada']) > 0 and
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

<xsl:text>
from named_types.</xsl:text>
<xsl:value-of select="translate(TypeName,'.','_')"/>
<xsl:text> import </xsl:text>
<xsl:value-of select="$python-class-name"/>
</xsl:for-each>

<xsl:text>


__all__ = [
    "RemainingElecEvent",</xsl:text>


<xsl:for-each select="$airtable//VersionedTypes/VersionedType[
  count(Protocols[text()='scada']) > 0 and
  (Status = 'Active' or Status = 'Pending') and
  (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial')
]">
<xsl:sort select="VersionedTypeName" data-type="text"/>

<xsl:variable name="python-class-name">
<xsl:choose>
<xsl:when test="(normalize-space(PythonClassName) ='')">
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="TypeName" />
</xsl:call-template>
</xsl:when>
<xsl:otherwise>
<xsl:value-of select="normalize-space(PythonClassName)" />
</xsl:otherwise>
</xsl:choose>
</xsl:variable>


<xsl:text>
    "</xsl:text>
    <xsl:value-of select="$python-class-name"/>
    <xsl:text>",</xsl:text>


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
