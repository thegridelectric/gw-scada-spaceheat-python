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
                    <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/enums/__init__.py</xsl:text></xsl:element>

                <OverwriteMode>Always</OverwriteMode>
                <xsl:element name="FileContents">
<xsl:text>"""
GridWorks Type Registry Enums used in Spaceheat SCADA code
"""

# Enums from gwproto</xsl:text>

<xsl:for-each select="$airtable//ProtocolEnums/ProtocolEnum[(normalize-space(ProtocolName) ='gwproto')]">
<xsl:sort select="LocalEnumName" data-type="text"/>
<xsl:text>
from gwproto.enums.</xsl:text>
<xsl:value-of select="translate(LocalEnumName,'.','_')"/>
<xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="LocalEnumName" />
</xsl:call-template>


</xsl:for-each>

<xsl:text>

# Enums from scada</xsl:text>
<xsl:for-each select="$airtable//ProtocolEnums/ProtocolEnum[(normalize-space(ProtocolName) ='scada')]">
<xsl:sort select="LocalEnumName" data-type="text"/>
<xsl:text>
from enums.</xsl:text>
<xsl:value-of select="translate(LocalEnumName,'.','_')"/>
<xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="type-name-text" select="LocalEnumName" />
</xsl:call-template>


</xsl:for-each>
<xsl:text>


__all__ = [</xsl:text>
<xsl:for-each select="$airtable//ProtocolEnums/ProtocolEnum[(normalize-space(ProtocolName) ='gwproto')]">
<xsl:sort select="LocalEnumName" data-type="text"/>
<xsl:variable name="gt-enum-id" select="GtEnumId"/>



<xsl:text>
    "</xsl:text>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="type-name-text" select="LocalEnumName" />
    </xsl:call-template>
    <xsl:text>",  # [</xsl:text>
    <xsl:value-of select="EnumName"/><xsl:text> version </xsl:text>
    <xsl:value-of select="EnumVersion"/>
    <xsl:text>](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#</xsl:text>
    <xsl:value-of select="translate(EnumName,'.','')"/>
    <xsl:text>)</xsl:text>
</xsl:for-each>

<xsl:for-each select="$airtable//ProtocolEnums/ProtocolEnum[(normalize-space(ProtocolName) ='scada')]">
<xsl:sort select="LocalEnumName" data-type="text"/>
<xsl:variable name="gt-enum-id" select="GtEnumId"/>



<xsl:text>
    "</xsl:text>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="type-name-text" select="LocalEnumName" />
    </xsl:call-template>
    <xsl:text>",  # [</xsl:text>
    <xsl:value-of select="EnumName"/><xsl:text>.</xsl:text>
    <xsl:value-of select="EnumVersion"/>
    <xsl:text>](https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#</xsl:text>
    <xsl:value-of select="translate(EnumName,'.','')"/>
    <xsl:text>)</xsl:text>
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
