<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns:msxsl="urn:schemas-microsoft-com:xslt" exclude-result-prefixes="msxsl" xmlns:xs="http://www.w3.org/2001/XMLSchema">
    <xsl:output method="xml" indent="yes" />



<xsl:template name="python-case">
    <xsl:param name="camel-case-text" select="''"></xsl:param>
    <xsl:param name="is_first" select="'true'"></xsl:param>
    <xsl:variable name="next-char" select="substring($camel-case-text, 1, 1)" />
    <xsl:if test="(normalize-space($is_first) != 'true') and (translate($next-char, $ucletters, $lcletters) != $next-char)">
        <xsl:text>_</xsl:text>
    </xsl:if>
    <xsl:value-of select="translate($next-char, $ucletters, $lcletters)"/>
    <xsl:if test="string-length($camel-case-text) >= 2">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="substring($camel-case-text, 2, string-length($camel-case-text))" />
            <xsl:with-param name="is_first" select="'false'" />
        </xsl:call-template>
    </xsl:if>
</xsl:template>

<xsl:template name="upper-python-case">
    <xsl:param name="camel-case-text" select="''"></xsl:param>
    <xsl:variable name="python-case">
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="translate($camel-case-text, '.', '')" />
        </xsl:call-template>
    </xsl:variable>
    <xsl:value-of select="translate($python-case, $lcletters, $ucletters)"/>
</xsl:template>

<xsl:template name="wrap-text">
    <xsl:param name="text"></xsl:param>
    <xsl:param name="index" select="1" />
    <xsl:variable name="next-char" select="substring($text, 1, 1)" />
    <xsl:value-of select="$next-char"/>
    <xsl:choose>
        <xsl:when test="$next-char = ' ' and $index > 70" xml:space="preserve">
        <xsl:if test="string-length($text) > 1" xml:space="default">
            <xsl:call-template name="wrap-text">
                <xsl:with-param name="text" select="substring($text, 2, string-length($text))" />
                <xsl:with-param name="index" select="1" />
            </xsl:call-template></xsl:if></xsl:when>
            <xsl:otherwise>
                <xsl:if test="string-length($text) > 1">
                    <xsl:call-template name="wrap-text">
                        <xsl:with-param name="text" select="substring($text, 2, string-length($text))" />
                        <xsl:with-param name="index" select="$index + 1" />
                    </xsl:call-template>
                </xsl:if>
            </xsl:otherwise>
    </xsl:choose>
</xsl:template>


<xsl:template name="message-case">
    <xsl:param name="mp-schema-text" select="''"></xsl:param>
    <xsl:param name="is_first" select="'true'"></xsl:param>
    <xsl:variable name="next-char" select="substring($mp-schema-text, 1, 1)" />
    <xsl:if test="(normalize-space($is_first) = 'true')">
        <xsl:value-of select="translate($next-char, $lcletters, $ucletters)"/>
    </xsl:if>
     <xsl:if test="(normalize-space($next-char) = '.')">
        <xsl:text>_</xsl:text>
         <xsl:if test="string-length($mp-schema-text) >= 2">
             <xsl:call-template name="message-case">
                <xsl:with-param name="mp-schema-text" select="substring($mp-schema-text, 2, string-length($mp-schema-text))" />
                <xsl:with-param name="is_first" select="'true'" />
             </xsl:call-template>
         </xsl:if>
    </xsl:if>
    <xsl:if test="(normalize-space($next-char) != '.')">
        <xsl:if test="(normalize-space($is_first) != 'true')"> <xsl:value-of select="$next-char"/></xsl:if>
            <xsl:if test="string-length($mp-schema-text) >= 2">
                 <xsl:call-template name="message-case">
                    <xsl:with-param name="mp-schema-text" select="substring($mp-schema-text, 2, string-length($mp-schema-text))" />
                    <xsl:with-param name="is_first" select="'false'" />
                </xsl:call-template>
            </xsl:if>
    </xsl:if>
</xsl:template>

<xsl:template name="payload-case">
    <xsl:param name="mp-schema-text"/>
    <xsl:variable name="msg-case">
        <xsl:call-template name="message-case">
            <xsl:with-param name="mp-schema-text" select="$mp-schema-text"/>
        </xsl:call-template>
    </xsl:variable>
    <xsl:value-of select="translate($msg-case,'_','')"/>
</xsl:template>

<xsl:template name="axiom-def">
    <xsl:param name="axiom-name"></xsl:param>
    <xsl:variable name="airtable-matching-axiom" select="$airtable//Axioms/Axiom[Alias=$axiom-name]"/>
    <xsl:text>"""From Airtable Axioms: </xsl:text>
        <xsl:call-template name="wrap-text">
            <xsl:with-param name="text" select="$airtable-matching-axiom/Description"/>
        </xsl:call-template><xsl:text> """</xsl:text>
</xsl:template>

<xsl:template name="python-type">
    <xsl:param name="gw-type" select="String"/>
    <xsl:if test="$gw-type='String'"><xsl:text>str</xsl:text></xsl:if>
    <xsl:if test="$gw-type='Boolean'"><xsl:text>bool</xsl:text></xsl:if>
    <xsl:if test="$gw-type='Number'"><xsl:text>float</xsl:text></xsl:if>
    <xsl:if test="$gw-type='Integer'"><xsl:text>int</xsl:text></xsl:if>
    <xsl:if test="$gw-type='List'"><xsl:text>list</xsl:text></xsl:if>
    <xsl:if test="$gw-type='Dict'"><xsl:text>dict</xsl:text></xsl:if>
    <xsl:if test="not ($gw-type='String') and not ($gw-type='Boolean') and not ($gw-type='Number') and not ($gw-type='Integer') and not ($gw-type='List')">
        <xsl:value-of select="TypeInPayload"/>
    </xsl:if>
</xsl:template>

<xsl:template name="nt-case">
    <xsl:param name="mp-schema-text" select="''"></xsl:param>
    <xsl:variable name="as-class-name">
        <xsl:call-template name="message-case">
            <xsl:with-param name="mp-schema-text" select="$mp-schema-text" />
        </xsl:call-template>
    </xsl:variable>
    <xsl:value-of select="translate($as-class-name,'_','')"/>
</xsl:template>
</xsl:stylesheet>