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


<xsl:template name="wrap-quoted-text">
    <xsl:param name="text"/>
    <xsl:param name="min-line-length" select="90"/>
    <xsl:param name="indent-spaces" select="4"/>
    <xsl:param name="index" select="1"/>

    <xsl:variable name="allowed-chars" select="$min-line-length - $indent-spaces"/>
    <xsl:variable name="this-char" select="substring($text, 1, 1)"/>


    <!-- Output the current character -->
    <xsl:value-of select="$this-char"/>

    <xsl:if test="string-length($text) > 1">

    <xsl:variable name="next-char" select="substring($text, 2, 1)"/>
    <xsl:choose>
            <xsl:when test="$next-char = ' ' and $index > $allowed-chars">
                    <!-- When next character is a space and we are at or beyond a min line length-->
                    <!-- .... add end quote, comma, return-->
                    <xsl:text> "&#xA;</xsl:text>
                    <!-- ... insert the specified number of indent spaces -->
                    <xsl:call-template name="insert-spaces">
                        <xsl:with-param name="count" select="$indent-spaces"/>
                    </xsl:call-template>
                    <!-- .... and then start the lext line with a quote-->
                    <xsl:text>"</xsl:text>

                    <!-- Reset the character index to 1, and jump over the next character (since it is a space) -->
                    <xsl:call-template name="wrap-quoted-text">
                        <xsl:with-param name="text" select="substring($text, 3)"/>
                        <xsl:with-param name="min-line-length" select="$min-line-length"/>
                        <xsl:with-param name="indent-spaces" select="$indent-spaces"/>
                        <xsl:with-param name="index" select="1"/>
                    </xsl:call-template>

            </xsl:when>
            <xsl:otherwise>
                    <!-- Otherwise, move onto the next character, updating the character index by 1 -->
                    <xsl:call-template name="wrap-quoted-text">
                        <xsl:with-param name="text" select="substring($text, 2)"/>
                        <xsl:with-param name="min-line-length" select="$min-line-length"/>
                        <xsl:with-param name="indent-spaces" select="$indent-spaces"/>
                        <xsl:with-param name="index" select="$index + 1"/>
                    </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:if>
</xsl:template>




<xsl:template name="wrap-text">
    <xsl:param name="text"/>
    <xsl:param name="min-line-length" select="90"/>
    <xsl:param name="indent-spaces" select="4"/>
    <xsl:param name="index" select="1"/>
    <xsl:param name="is-first-line" select="1"/>
    <xsl:param name="first-line-shorter-by" select="0"/>

    <xsl:variable name="allowed-chars">
	<xsl:choose>
	<xsl:when test= "$is-first-line = '1'">
		<xsl:value-of select="$min-line-length - $indent-spaces - $first-line-shorter-by"/>
	</xsl:when>
	<xsl:otherwise>
		<xsl:value-of select="$min-line-length - $indent-spaces"/>
	</xsl:otherwise>
    </xsl:choose>
	</xsl:variable>

    <xsl:variable name="this-char" select="substring($text, 1, 1)"/>

    <!-- Output the current character -->
    <xsl:value-of select="$this-char"/>

    <xsl:if test="string-length($text) > 1">

    <xsl:variable name="next-char" select="substring($text, 2, 1)"/>
    <xsl:choose>
            <xsl:when test="$next-char = ' ' and $index > $allowed-chars">
                    <!-- When next character is a space and we are at or beyond a min line length, create carriage return -->
                    <xsl:text>&#xA;</xsl:text>

                    <!-- ... and insert the specified number of indent spaces -->
                    <xsl:call-template name="insert-spaces">
                        <xsl:with-param name="count" select="$indent-spaces"/>
                    </xsl:call-template>

                    <!-- Reset the character index to 1, and jump over the next character (since it is a space) -->
                    <xsl:call-template name="wrap-text">
                        <xsl:with-param name="text" select="substring($text, 3)"/>
                        <xsl:with-param name="min-line-length" select="$min-line-length"/>
                        <xsl:with-param name="indent-spaces" select="$indent-spaces"/>
                        <xsl:with-param name="index" select="1"/>
                        <xsl:with-param name="is-first-line" select="0"/>
                        <xsl:with-param name="first-line-shorter-by" select="$first-line-shorter-by"/>
                    </xsl:call-template>

            </xsl:when>
            <xsl:otherwise>
                    <!-- Otherwise, move onto the next character, updating the character index by 1 -->
                    <xsl:call-template name="wrap-text">
                        <xsl:with-param name="text" select="substring($text, 2)"/>
                        <xsl:with-param name="min-line-length" select="$min-line-length"/>
                        <xsl:with-param name="indent-spaces" select="$indent-spaces"/>
                        <xsl:with-param name="index" select="$index + 1"/>
                        <xsl:with-param name="is-first-line" select="$is-first-line"/>
                        <xsl:with-param name="first-line-shorter-by" select="$first-line-shorter-by"/>
                    </xsl:call-template>
            </xsl:otherwise>
        </xsl:choose>
    </xsl:if>
</xsl:template>

<xsl:template name="insert-spaces">
    <xsl:param name="count" select="4"/>
    <xsl:if test="$count > 0">
        <xsl:text> </xsl:text>
        <xsl:call-template name="insert-spaces">
            <xsl:with-param name="count" select="$count - 1"/>
        </xsl:call-template>
    </xsl:if>
</xsl:template>

<xsl:template name="message-case">
    <xsl:param name="type-name-text" select="''"></xsl:param>
    <xsl:param name="is_first" select="'true'"></xsl:param>
    <xsl:variable name="next-char" select="substring($type-name-text, 1, 1)" />
    <xsl:if test="(normalize-space($is_first) = 'true')">
        <xsl:value-of select="translate($next-char, $lcletters, $ucletters)"/>
    </xsl:if>
     <xsl:if test="(normalize-space($next-char) = '.')">
        <xsl:text>_</xsl:text>
         <xsl:if test="string-length($type-name-text) >= 2">
             <xsl:call-template name="message-case">
                <xsl:with-param name="type-name-text" select="substring($type-name-text, 2, string-length($type-name-text))" />
                <xsl:with-param name="is_first" select="'true'" />
             </xsl:call-template>
         </xsl:if>
    </xsl:if>
    <xsl:if test="(normalize-space($next-char) != '.')">
        <xsl:if test="(normalize-space($is_first) != 'true')"> <xsl:value-of select="$next-char"/></xsl:if>
            <xsl:if test="string-length($type-name-text) >= 2">
                 <xsl:call-template name="message-case">
                    <xsl:with-param name="type-name-text" select="substring($type-name-text, 2, string-length($type-name-text))" />
                    <xsl:with-param name="is_first" select="'false'" />
                </xsl:call-template>
            </xsl:if>
    </xsl:if>
</xsl:template>

<xsl:template name="payload-case">
    <xsl:param name="type-name-text"/>
    <xsl:variable name="msg-case">
        <xsl:call-template name="message-case">
            <xsl:with-param name="type-name-text" select="$type-name-text"/>
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

<xsl:template name="gwapi-type">
    <xsl:param name="gw-type" select="String"/>
    <xsl:if test="$gw-type='String'"><xsl:text>string</xsl:text></xsl:if>
    <xsl:if test="$gw-type='Boolean'"><xsl:text>boolean</xsl:text></xsl:if>
    <xsl:if test="$gw-type='Number'"><xsl:text>number</xsl:text></xsl:if>
    <xsl:if test="$gw-type='Integer'"><xsl:text>integer</xsl:text></xsl:if>
    <xsl:if test="$gw-type='Dict'"><xsl:text>dict</xsl:text></xsl:if>
    <xsl:if test="not ($gw-type='String') and not ($gw-type='Boolean') and not ($gw-type='Number') and not ($gw-type='Integer')">
        <xsl:value-of select="$gw-type"/>
    </xsl:if>
</xsl:template>

<xsl:template name="nt-case">
    <xsl:param name="type-name-text" select="''"></xsl:param>
    <xsl:variable name="as-class-name">
        <xsl:call-template name="message-case">
            <xsl:with-param name="type-name-text" select="$type-name-text" />
        </xsl:call-template>
    </xsl:variable>
    <xsl:value-of select="translate($as-class-name,'_','')"/>
</xsl:template>



</xsl:stylesheet>
