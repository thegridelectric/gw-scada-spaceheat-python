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
                <xsl:for-each select="$airtable//ProtocolEnums/ProtocolEnum[(normalize-space(ProtocolName) ='scada')]">
                <xsl:variable name="versioned-enum-id" select="VersionedEnum"/>
                <xsl:for-each select="$airtable//VersionedEnums/VersionedEnum[(VersionedEnumId = $versioned-enum-id)  and (Status = 'Active' or Status = 'Pending')]">
                    <xsl:variable name="enum-name" select="EnumName"/>
                    <xsl:variable name="enum-name-style" select="PythonEnumNameStyle" />
                    <xsl:variable name="enum-id" select="GtEnumId"/>
                    <xsl:variable name="description" select="Description"/>
                    <xsl:variable name="url" select="Url"/>
                    <xsl:variable name="default-enum-value" select="DefaultEnumValue"/>
                     <xsl:variable name="version" select="Version"/>
                <xsl:variable name="overwrite-mode">

                    <xsl:if test="not (Status = 'Pending')">
                    <xsl:text>Always</xsl:text>
                    </xsl:if>
                    <xsl:if test="(Status = 'Pending')">
                    <xsl:text>Always</xsl:text>
                    </xsl:if>
                    </xsl:variable>
                <FileSetFile>
                        <xsl:element name="RelativePath"><xsl:text>../../../../docs/asls/json/</xsl:text>
                            <xsl:value-of select="translate($enum-name,'.','-')"/><xsl:text>.json</xsl:text></xsl:element>

                    <OverwriteMode><xsl:value-of select="$overwrite-mode"/></OverwriteMode>
                    <xsl:element name="FileContents">

<xsl:text>{
    "gtr_asl": "001",
    "enum_name": "</xsl:text>
        <xsl:value-of select="$enum-name"/><xsl:text>",
    "enum_version": "</xsl:text><xsl:value-of select="$version"/><xsl:text>",
    "description": "</xsl:text>
    <xsl:value-of select="normalize-space($description)"/><xsl:text>",</xsl:text>
    <xsl:if test="normalize-space(Url) !=''">
    <xsl:text>
    "url": "</xsl:text>
    <xsl:value-of select="normalize-space($url)"/>
    <xsl:text>",</xsl:text>
    </xsl:if><xsl:text>
    "ssot": "https://gridworks-type-registry.readthedocs.io/en/latest/enums.html#</xsl:text>
    <xsl:value-of select="translate(EnumName,'.','')"/>
    <xsl:text>",
    "values": [</xsl:text>
    <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $version)]">
    <xsl:sort select="Idx" data-type="number"/>
    <xsl:text>"</xsl:text>
    <xsl:value-of select="LocalValue"/>
    <xsl:text>"</xsl:text>
        <xsl:if test="position() != count($airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $version)])">
        <xsl:text>, </xsl:text>
    </xsl:if>

    </xsl:for-each>

    <xsl:text>],
    "value_to_symbol": {</xsl:text>

            <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $version)]">
            <xsl:sort select="Idx" data-type="number"/>
            <xsl:text> "</xsl:text>
            <xsl:if test="$enum-name-style = 'Upper'">
                <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
            </xsl:if>
            <xsl:if test="$enum-name-style ='UpperPython'">
                <xsl:value-of select="LocalValue"/>
            </xsl:if>
            <xsl:text>": "</xsl:text>
            <xsl:value-of select="Symbol"/><xsl:text>"</xsl:text>
            <xsl:if test="position() != count($airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $version)])">
                <xsl:text>, </xsl:text>
            </xsl:if>
            </xsl:for-each>
    <xsl:text>},
    "value_to_version": {</xsl:text>
            <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $version)]">
            <xsl:sort select="Idx" data-type="number"/>
            <xsl:text> "</xsl:text>
            <xsl:if test="$enum-name-style = 'Upper'">
                <xsl:value-of select="translate(translate(LocalValue,'-',''),$lcletters, $ucletters)"/>
            </xsl:if>
            <xsl:if test="$enum-name-style ='UpperPython'">
                <xsl:value-of select="LocalValue"/>
            </xsl:if>
            <xsl:text>": "</xsl:text>
            <xsl:value-of select="Version"/><xsl:text>"</xsl:text>
            <xsl:if test="position() != count($airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $version)])">
                <xsl:text>, </xsl:text>
            </xsl:if>
            </xsl:for-each>
    <xsl:text>},
    "value_descriptions": {</xsl:text>
            <xsl:for-each select="$airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $version)]">
            <xsl:sort select="Idx" data-type="number"/>
            <xsl:text>
                "</xsl:text><xsl:value-of select="LocalValue"/><xsl:text>": "</xsl:text>
                    <xsl:value-of select="normalize-space(Description)"/>
                    <xsl:if test="normalize-space(Url) !=''">
                    <xsl:text> More Info: </xsl:text>
                    <xsl:value-of select="normalize-space(Url)"/>
                    </xsl:if>
                    <xsl:text>"</xsl:text>
            <xsl:if test="position() != count($airtable//EnumSymbols/EnumSymbol[(Enum = $enum-id) and (Version &lt;= $version)])">
            <xsl:text>,</xsl:text>
            </xsl:if>
            </xsl:for-each>
            <xsl:text>
            },
    "default_value": "</xsl:text> <xsl:value-of select="$default-enum-value"/>
        <xsl:text>"
}</xsl:text>



                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>
                </xsl:for-each>
            </FileSetFiles>
        </FileSet>
    </xsl:template>



</xsl:stylesheet>
