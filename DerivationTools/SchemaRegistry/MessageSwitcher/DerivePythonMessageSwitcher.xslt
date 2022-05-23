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
    <xsl:include href="GwCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
        <FileSet>
            <FileSetFiles>
                <FileSetFile>
                    <xsl:element name="RelativePath"><xsl:text>../../../message_makers/message_protocol_switcher.py</xsl:text></xsl:element>
                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents">


                <xsl:for-each select="$airtable//MpSchemas/MpSchema[(normalize-space(Title) !='') and not(IsNamedTuple = 'true')  and ((Status = 'Active') or (Status = 'Supported') or (Status = 'Pending'))]">
                    <xsl:variable name="mp-alias" select="Alias" />
                    <xsl:variable name="mp-schema-id" select="MpSchemaId" />
                    <xsl:variable name="class-name">
                        <xsl:call-template name="message-case">
                            <xsl:with-param name="mp-schema-text" select="Alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="routing-key">
                        <xsl:if test="MessagePassingMechanism = 'SassyRabbit.2_0'">
                            <xsl:value-of select="translate(SassyTo, $ucletters, $lcletters)"/><xsl:text>.custom.</xsl:text>
                            <xsl:value-of select="translate(SassyFrom, $ucletters, $lcletters)"/><xsl:text>.</xsl:text>
                            <xsl:value-of select="translate(SassyMessage, $ucletters, $lcletters)"/>
                        </xsl:if>
                        <xsl:if test="MessagePassingMechanism = 'SassyRabbit.1_0'">
                            <xsl:value-of select="translate(SassyTo, $ucletters, $lcletters)"/><xsl:text>.general.</xsl:text>
                            <xsl:value-of select="translate(SassyFrom, $ucletters, $lcletters)"/><xsl:text>.</xsl:text>
                            <xsl:value-of select="translate(SassyMessage, $ucletters, $lcletters)"/>
                        </xsl:if>
                    </xsl:variable>
                    <xsl:variable name="class-as-folder">
                        <xsl:value-of select="SassyLexiconTermPythonFolderName"/>
                    </xsl:variable>

<xsl:text>
from message_makers.</xsl:text>
                    <xsl:value-of select="SassyLexiconTermPythonFolderName"/><xsl:text>.</xsl:text>
                    <xsl:value-of select="translate(Title,'.','_')"/><xsl:text>.</xsl:text>
                     <xsl:value-of select="translate(Alias,'.','_')"/><xsl:text> import \
    </xsl:text><xsl:value-of select="$class-name"/>
                </xsl:for-each>


<xsl:text>

def message_protocol_switcher(alias):
    switcher = {}</xsl:text>
                    <xsl:for-each select="$airtable//MpSchemas/MpSchema[(normalize-space(Title) !='') and not(IsNamedTuple = 'true') and ((Status = 'Active') or (Status = 'Supported') or (Status = 'Pending'))]">
                        <xsl:variable name="class-name">
                            <xsl:call-template name="message-case">
                                <xsl:with-param name="mp-schema-text" select="Alias" />
                            </xsl:call-template>
                        </xsl:variable>
                            <xsl:text>
    switcher['</xsl:text> <xsl:value-of select="Alias"/><xsl:text>'] = </xsl:text><xsl:value-of select="$class-name"  />
                    </xsl:for-each>

<xsl:text>

    func = switcher.get(alias, lambda: "No python implementation for message %s" % alias)
    return func
</xsl:text>


</xsl:element>
</FileSetFile>





            </FileSetFiles>
        </FileSet>
    </xsl:template>
    

</xsl:stylesheet>