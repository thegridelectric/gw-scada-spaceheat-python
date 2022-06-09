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
                <xsl:for-each select="$airtable//Schemas/Schema[(normalize-space(Alias) !='')  and (Status = 'Active') and (ProtocolType = 'Json')]">
                    <xsl:variable name="local-alias" select="AliasRoot" />  
                    <xsl:variable name="class-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="mp-schema-text" select="$local-alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../gw_spaceheat/schema/gt/</xsl:text>
                                <xsl:value-of select="translate($local-alias,'.','_')"/><xsl:text>/</xsl:text>
                                <xsl:value-of select="translate($local-alias,'.','_')"/><xsl:text>.py</xsl:text></xsl:element>

                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents">

   
<xsl:text>"""</xsl:text><xsl:value-of select="$local-alias"/><xsl:text> type"""

from schema.errors import MpSchemaError
from schema.gt.</xsl:text> <xsl:value-of select="translate($local-alias,'.','_')"/>
<xsl:text>.</xsl:text><xsl:value-of select="translate($local-alias,'.','_')"/>
<xsl:text>_base import </xsl:text><xsl:value-of select="$class-name"/><xsl:text>Base


class </xsl:text>
<xsl:value-of select="$class-name"/>
<xsl:text>(</xsl:text>
<xsl:value-of select="$class-name"/>
<xsl:text>Base):

    def check_for_errors(self):
        errors = self.derived_errors() + self.hand_coded_errors()
        if len(errors) > 0:
            raise MpSchemaError(f" Errors making making </xsl:text>
            <xsl:value-of select="$local-alias"/>
            <xsl:text> for {self}: {errors}")

    def hand_coded_errors(self):
        return []
</xsl:text>


                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>