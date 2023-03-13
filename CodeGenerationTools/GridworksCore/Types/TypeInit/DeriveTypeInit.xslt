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
                    <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/schema/__init__.py</xsl:text></xsl:element>

                <OverwriteMode>Always</OverwriteMode>
                <xsl:element name="FileContents">
<xsl:text>""" List of all the schema types """
</xsl:text>
<xsl:for-each select="$airtable//ProtocolTypes/ProtocolType[(normalize-space(ProtocolName) ='scada')]">
<xsl:sort select="TypeName" data-type="text"/>
<xsl:variable name="schema-id" select="Type"/>
<xsl:for-each select="$airtable//Schemas/Schema[(SchemaId = $schema-id)  and (Status = 'Active' or Status = 'Pending') and (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial') and not (NotInInit='true')]">

<xsl:variable name="local-alias" select="AliasRoot" />

<xsl:text>
from schema.</xsl:text>
<xsl:value-of select="translate(AliasRoot,'.','_')"/>
<xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="AliasRoot" />
</xsl:call-template>
<xsl:text>
from schema.</xsl:text>
<xsl:value-of select="translate(AliasRoot,'.','_')"/>
<xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="AliasRoot" />
</xsl:call-template>
<xsl:text>_Maker</xsl:text>
</xsl:for-each>
</xsl:for-each>
<xsl:text>


__all__ = [</xsl:text>
<xsl:for-each select="$airtable//ProtocolTypes/ProtocolType[(normalize-space(ProtocolName) ='scada')]">
<xsl:sort select="TypeName" data-type="text"/>
<xsl:variable name="schema-id" select="Type"/>
<xsl:for-each select="$airtable//Schemas/Schema[(SchemaId = $schema-id)  and (Status = 'Active' or Status = 'Pending') and (ProtocolCategory = 'Json' or ProtocolCategory = 'GwAlgoSerial')]">
<xsl:variable name="local-alias" select="AliasRoot" />
<xsl:if test="not(NotInInit='true')">
<xsl:text>
    "</xsl:text>
</xsl:if>
<xsl:if test="(NotInInit='true')">
<xsl:text>
    # "</xsl:text>
</xsl:if>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="mp-schema-text" select="AliasRoot" />
    </xsl:call-template>
    <xsl:text>",</xsl:text>
<xsl:if test="not(NotInInit='true')">
<xsl:text>
    "</xsl:text>
</xsl:if>
<xsl:if test="(NotInInit='true')">
<xsl:text>
    # "</xsl:text>
</xsl:if>
    <xsl:call-template name="nt-case">
        <xsl:with-param name="mp-schema-text" select="AliasRoot" />
    </xsl:call-template>
    <xsl:text>_Maker",</xsl:text>
</xsl:for-each>
</xsl:for-each>
<xsl:text>
]

</xsl:text>



                </xsl:element>
            </FileSetFile>


        </FileSet>
    </xsl:template>


</xsl:stylesheet>
