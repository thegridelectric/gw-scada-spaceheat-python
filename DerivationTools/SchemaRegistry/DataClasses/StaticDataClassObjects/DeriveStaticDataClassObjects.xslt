<?xml version="1.0" encoding="utf-8"?>
<xsl:stylesheet version="1.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
    xmlns:msxsl="urn:schemas-microsoft-com:xslt" exclude-result-prefixes="msxsl"
>
    <xsl:output method="xml" indent="yes"/>
    <xsl:include href="../CommonXsltTemplates.xslt"/>

    <xsl:variable name="airtable" select="/" />
    <xsl:variable name="airtable-from-doc" select="document('Airtable.xml')" />
    <xsl:variable name="odxml" select="document('DataSchema.odxml')" />
    <xsl:variable name="double_quote">"</xsl:variable>
    <xsl:variable name="single_quote">'</xsl:variable>
    <xsl:include href="GwSchemaCommon.xslt"/>

    <xsl:template match="@* | node()">
        <xsl:copy>
            <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
    </xsl:template>

    <xsl:template match="/*">
        <FileSet>
            <FileSetFiles>
                <xsl:for-each select="//GwEntities/GwEntity[normalize-space(AllObjectsStatic) = 'true' and ScadaUses = 'true']">
                <xsl:variable name="entity" select="." />
                <xsl:variable name="entity-name" select="Name"/>
                <xsl:variable name="entity-plural-name" select="PluralName"/>
                <xsl:variable name="od" select="$odxml//ObjectDefs/ObjectDef[Name=$entity/Name]"/>
                <xsl:variable name="read-only-properties" select="$od//PropertyDef[(normalize-space(IsReadonly) = 'true' or normalize-space(MatchingMetaData/IsReadonly) = 'true')]"/>
                <xsl:variable name="basic-string-properties" select="$od//PropertyDef[normalize-space(IsCollection) != 'true' and normalize-space(MatchingMetaData/IsCollection) != 'true' and normalize-space(IsReadonly) != 'true' and normalize-space(MatchingMetaData/IsReadonly) != 'true' and IsPrimaryKey = 0 and count(Relationships)=0  and Name != 'Definition' and Name !='Description' and DataType = 'String']"/>o
                <xsl:variable name="basic-boolean-properties" select="$od//PropertyDef[normalize-space(IsCollection) != 'true' and normalize-space(MatchingMetaData/IsCollection) != 'true' and normalize-space(IsReadonly) != 'true' and normalize-space(MatchingMetaData/IsReadonly) != 'true' and IsPrimaryKey = 0 and count(Relationships)=0  and Name != 'Definition' and Name !='Description' and DataType = 'Boolean']"/>
                <xsl:variable name="basic-number-properties" select="$od//PropertyDef[normalize-space(IsCollection) != 'true' and normalize-space(MatchingMetaData/IsCollection) != 'true' and normalize-space(IsReadonly) != 'true' and normalize-space(MatchingMetaData/IsReadonly) != 'true' and IsPrimaryKey = 0 and count(Relationships)=0  and Name != 'Definition' and Name !='Description' and (DataType = 'Float' or DataType = 'Number' or DataType = 'Decimal' or DataType = 'Int' or DataType = 'Int16' or DataType = 'Int32' )]"/>
                <xsl:variable name="foreign-keys" select="$od//PropertyDef[normalize-space(MatchingMetaData/RelationshipType)='One' and normalize-space(IsCollection) != 'true' and count(Relationships)>0 and normalize-space(MatchingMetaData/IsCollection) != 'true']"/>


                <xsl:variable name="primary-key-name">
                    <xsl:call-template name="python-case"><xsl:with-param name="camel-case-text" select="$entity/PrimaryKeyName"/> </xsl:call-template>
                </xsl:variable>
                <xsl:variable name="primary-key-camel" select="$entity/PrimaryKeyName"/>

                <FileSetFile>
                    <RelativePath>
                        <xsl:text>../../../../gw_spaceheat/data_classes/</xsl:text><xsl:value-of select="PythonName"/><xsl:text>_static.py</xsl:text>
                    </RelativePath>
                    <xsl:element name="FileContents">
                        <xsl:text>from typing import Dict
from data_classes.</xsl:text><xsl:value-of select="PythonName"/><xsl:text> import </xsl:text><xsl:value-of select="Name"/><xsl:text>
Platform</xsl:text><xsl:value-of select="$entity/Name"/><xsl:text>: Dict[str,</xsl:text><xsl:value-of select="Name"/> <xsl:text>] = {}</xsl:text>  

 
                           <xsl:for-each select="//*[name()=$entity/PluralName]/*[name()=$entity/Name]">

                           <xsl:variable name="static-object" select="."/>
                           <xsl:variable name="static-name">
                               <xsl:variable name="static-name-with-spaces">
                               <xsl:if test="count(Alias) > 0">
                                   <xsl:call-template name="upper-python-case">
                                       <xsl:with-param name="camel-case-text" select="translate(Alias,'.','__')" />
                                   </xsl:call-template>
                               </xsl:if>
                               <xsl:if test="count(Value) > 0">
                                   <xsl:call-template name="upper-python-case">
                                       <xsl:with-param name="camel-case-text" select="Value" />
                                   </xsl:call-template>
                               </xsl:if>
                               </xsl:variable>
                               <xsl:value-of select="translate($static-name-with-spaces,' ','_')"/>
                           </xsl:variable>

                            <xsl:if test="not($static-name='') and $static-name">
<xsl:text>


"""</xsl:text><xsl:value-of select="$static-name"/>

<xsl:if test="count(Description) > 0">
<xsl:text>: </xsl:text>
                            <xsl:call-template name="wrap-text">
                                <xsl:with-param name="text" select="Description" />
                            </xsl:call-template>

</xsl:if>
<xsl:if test="count(Definition) > 0">
<xsl:text>: </xsl:text>

                            <xsl:call-template name="wrap-text">
                                <xsl:with-param name="text" select="translate(Definition,$double_quote,$single_quote)" />
                            </xsl:call-template>
</xsl:if>

<xsl:text>
"""
</xsl:text>


         <xsl:value-of select="$static-name"/>
                            <xsl:text> = </xsl:text><xsl:value-of select="$entity/Name"/><xsl:text>(</xsl:text> 
                            <xsl:for-each select="$basic-string-properties">
                            <xsl:variable name="pd" select="." />
                            <xsl:if test="$static-object/*[name() = $pd/Name] and $static-object/*[name() = $pd/Name] !=''">  
                      
                                <xsl:if test="position() &lt; (count($basic-string-properties)+1) and position() > 1"><xsl:text>,
                    </xsl:text></xsl:if>
                                <xsl:call-template name="python-case">
                                    <xsl:with-param name="camel-case-text" select="Name" />
                                </xsl:call-template>
                                <xsl:text> = "</xsl:text><xsl:value-of select="$static-object/*[name() = $pd/Name]" /><xsl:text>"</xsl:text>
                            </xsl:if>
                            </xsl:for-each>
                            <xsl:for-each select="$basic-boolean-properties">
                            <xsl:variable name="pd" select="." />
                            <xsl:if test="position() &lt; (count($basic-boolean-properties)+1)"><xsl:text>,
                    </xsl:text></xsl:if>
                                <xsl:call-template name="python-case">
                                    <xsl:with-param name="camel-case-text" select="Name" />
                                </xsl:call-template>
                                <xsl:text> = </xsl:text>
                                <xsl:if test="$static-object/*[name() = $pd/Name] = 'true'"> 
                                    <xsl:text>True</xsl:text>
                                </xsl:if>
                                <xsl:if test="not($static-object/*[name() = $pd/Name] = 'true')"> 
                                    <xsl:text>False</xsl:text>
                                </xsl:if>                               
                            </xsl:for-each>
                            <xsl:for-each select="$basic-number-properties">
                                <xsl:variable name="pd" select="." />
                                <xsl:if test="$static-object/*[name() = $pd/Name] and $static-object/*[name() = $pd/Name] !=''">  
                                    <xsl:if test="position() &lt; (count($basic-number-properties)+1)"><xsl:text>,
                    </xsl:text></xsl:if>
                                        <xsl:call-template name="python-case">
                                            <xsl:with-param name="camel-case-text" select="Name" />
                                        </xsl:call-template>
                                        <xsl:text> = </xsl:text>
                                        <xsl:value-of select="$static-object/*[name() = $pd/Name]" />        
                                    </xsl:if>    
                            </xsl:for-each>
                            <xsl:for-each select="$foreign-keys">
                                <xsl:variable name="foreign-object-name" select="Relationships/Relationship/ReferencedObjectDef"/>    
                                <xsl:variable name="foreign-gw-entity" select="$airtable//GwEntities/GwEntity[Name=$foreign-object-name]"/>
                                <xsl:variable name="foreign-key-name" select="$foreign-gw-entity/PrimaryKeyName"/>
                                <xsl:variable name="pd" select="." />
                                
                                <xsl:if test="$static-object/*[name() = $pd/Name] and $static-object/*[name() = $pd/Name] !=''">  
                                    <xsl:if test="position() &lt; (count($foreign-keys)+1)"><xsl:text>,
                    </xsl:text></xsl:if>
                                        <xsl:call-template name="python-case">
                                            <xsl:with-param name="camel-case-text" select="Name" />
                                        </xsl:call-template>
                                        <xsl:text>_</xsl:text>
                                        <xsl:call-template name="python-case">
                                            <xsl:with-param name="camel-case-text" select="$foreign-gw-entity/PrimaryKeyName"/>
                                        </xsl:call-template>
                                        <xsl:text> = </xsl:text>
                                        <xsl:variable name="reference-object-id" select="$static-object/*[name() = $pd/Name]" />
                                        <xsl:for-each select="$airtable/Airtable/*[name()=$foreign-gw-entity/PluralName]/*[name()=$foreign-gw-entity/Name]">
                                        <xsl:variable name="this-id" select="*[name() = concat($foreign-object-name,'Id')]"/>  
                                        <xsl:if test="$this-id = $reference-object-id">
                                                <xsl:text>"</xsl:text><xsl:value-of select="*[name()=$foreign-key-name]"/> <xsl:text>"</xsl:text> 
                                            </xsl:if>
                                        </xsl:for-each>
                                    </xsl:if>    
                            </xsl:for-each>


                            
<xsl:text>) 

Platform</xsl:text><xsl:value-of select="$entity/Name"/><xsl:text>[</xsl:text>
                            <xsl:value-of select="$static-name"/>
                            <xsl:text>.</xsl:text><xsl:value-of select="$primary-key-name"/><xsl:text>] = </xsl:text> <xsl:value-of select="$static-name"/>
                        </xsl:if>
                        </xsl:for-each>

                    </xsl:element>
                </FileSetFile>
                </xsl:for-each>
            </FileSetFiles>
        </FileSet>
    </xsl:template>

</xsl:stylesheet>
