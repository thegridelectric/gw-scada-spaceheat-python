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
    <xsl:include href="GwSchemaCommon.xslt"/>

    <xsl:template match="@*|node()">
        <xsl:copy>
            <xsl:apply-templates select="@*|node()" />
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/">
        <FileSet>
            <FileSetFiles>
                <xsl:for-each select="$airtable//MpSchemas/MpSchema[(normalize-space(Alias) !='')  and (FromDataClass='true') and ((Alias = 'gt.component.1_1_0')  or (Alias = 'gt.component.attribute.class.1_1_0')) and ((Status = 'Active') or (Status = 'Supported') or (Status = 'Pending'))]">
                    <xsl:variable name="mp-schema-alias" select="Alias" />  
                    <xsl:variable name="mp-schema-id" select="MpSchemaId" />
                    <xsl:variable name="class-name">
                        <xsl:call-template name="message-case">
                            <xsl:with-param name="mp-schema-text" select="Alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="nt-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="mp-schema-text" select="Alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="routing-key-base">
                        <xsl:if test="MessagePassingMechanism = 'SassyRabbit.3_0'">
                            <xsl:value-of select="translate(SassyFrom, $ucletters, $lcletters)"/><xsl:text>.</xsl:text>
                            <xsl:value-of select="translate(SassyMessage, $ucletters, $lcletters)"/><xsl:text>.</xsl:text>
                           <xsl:value-of select="translate(SassyTo, $ucletters, $lcletters)"/>
                       </xsl:if>
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
                    <FileSetFile>
                                <xsl:element name="RelativePath"><xsl:text>../../../gw_spaceheat/schema/gt/gnr/</xsl:text><xsl:value-of select="NtClass"/><xsl:text>/</xsl:text>
                                <xsl:value-of select="translate(Alias,'.','_')"/><xsl:text>_schema.py</xsl:text></xsl:element>

                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents">

   
<xsl:text>"""</xsl:text><xsl:value-of select="$mp-schema-alias"/><xsl:text> Schema"""
from typing import List, Tuple, Optional</xsl:text>

<xsl:text>
from schema.gt.gnr.</xsl:text><xsl:value-of select="NtClass"/>
<xsl:text>.</xsl:text><xsl:value-of select="translate(Alias,'.','_')"/>
<xsl:text>_schema_base import SchemaBase</xsl:text>


<xsl:if test="(IsNamedTuple='true')">
<xsl:text>


class </xsl:text>
<xsl:value-of select="$nt-name"/>
<xsl:text>(SchemaBase):</xsl:text></xsl:if>
<xsl:if test="not (IsNamedTuple='true')">
<xsl:text>


class Schema(PayloadBase):</xsl:text></xsl:if>
<xsl:text>
    def is_valid(self) -> Tuple[bool, Optional[List[str]]]:
        is_valid, errors = self.passes_derived_validations()</xsl:text>
        <xsl:for-each select="$airtable//MpSchemaAxioms/MpSchemaAxiom[MpSchemaAlias=$mp-schema-alias and not(normalize-space(AxiomAlias) = '')]">
        <xsl:text>
        next_is_valid, next_errors = self.</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="AxiomAlias"/>
        </xsl:call-template>
        <xsl:text>_validation()
        is_valid = is_valid and next_is_valid
        errors += next_errors</xsl:text>
</xsl:for-each>
        <xsl:text>
        if len(errors) > 0:
            errors.insert(0, 'Errors making </xsl:text><xsl:value-of select="$mp-schema-alias"/><xsl:text> type.')
        return is_valid, errors

    # hand-code schema axiom validations below</xsl:text>
    <xsl:for-each select="$airtable//MpSchemaAxioms/MpSchemaAxiom[MpSchemaAlias=$mp-schema-alias and not(normalize-space(AxiomAlias) = '')]">

    <xsl:text>
    def </xsl:text>
    <xsl:call-template name="python-case">
        <xsl:with-param name="camel-case-text" select="AxiomAlias"/>
    </xsl:call-template>
    <xsl:text>_validation(self)  -> Tuple[bool, Optional[List[str]]]:
        """</xsl:text>
        <xsl:if test="not(normalize-space(FormalStatement) = '')">
            <xsl:text>Formal Statement:  </xsl:text>
                <xsl:call-template name="wrap-text">
                    <xsl:with-param name="text" select="FormalStatement" />
                </xsl:call-template>
            </xsl:if>
        <xsl:if test="(normalize-space(FormalStatement) = '')">
        <xsl:call-template name="wrap-text">
            <xsl:with-param name="text" select="Description" />
        </xsl:call-template>
        </xsl:if>
        <xsl:text>"""
        return True, []
    </xsl:text>
    </xsl:for-each>


                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>


</xsl:stylesheet>