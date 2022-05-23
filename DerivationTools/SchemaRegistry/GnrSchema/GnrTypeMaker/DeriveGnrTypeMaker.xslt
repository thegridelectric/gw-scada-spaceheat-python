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
                <xsl:for-each select="$airtable//MpSchemas/MpSchema[(normalize-space(Alias) !='') and (FromDataClass='true') and (ScadaUses = 'true') and ((Status = 'Active') or (Status = 'Supported') or (Status = 'Pending'))]">
                    <xsl:variable name="mp-schema-alias" select="KafkaAlias" />  
                    <xsl:variable name="mp-schema-id" select="MpSchemaId" />
                    <xsl:variable name="class-name">
                        <xsl:call-template name="message-case">
                            <xsl:with-param name="mp-schema-text" select="Alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name='mp-schema-type'>
                        <xsl:if test="IsNamedTuple='true'">
                            <xsl:text>MessageSubset</xsl:text>
                        </xsl:if>
                        <xsl:if test="not (IsNamedTuple='true')">
                            <xsl:text>NotMessageSubset</xsl:text>
                        </xsl:if>
                    </xsl:variable>
                    <xsl:variable name="nt-name">
                        <xsl:call-template name="nt-case">
                            <xsl:with-param name="mp-schema-text" select="Alias" />
                        </xsl:call-template>
                    </xsl:variable>
                    <xsl:variable name="routing-key-base">
                        <xsl:if test="(MessagePassingMechanism = 'SassyRabbit.3_0') or (MessagePassingMechanism = 'GwService.1_0')">
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
                                <xsl:element name="RelativePath"><xsl:text>../../../../gw_spaceheat/schema/gt/gnr/</xsl:text><xsl:value-of select="NtClass"/><xsl:text>/</xsl:text>
                                <xsl:value-of select="translate(Alias,'.','_')"/><xsl:text>_maker.py</xsl:text></xsl:element>
                        <OverwriteMode>Always</OverwriteMode>
                        <xsl:element name="FileContents">

<xsl:text>"""Makes </xsl:text><xsl:value-of select="$mp-schema-alias"/><xsl:text> type.</xsl:text>
<xsl:if test="not (normalize-space(Description)='')">
<xsl:text>.
</xsl:text>
<xsl:call-template  name="wrap-text">
    <xsl:with-param name="text" select="Description"/>
</xsl:call-template>
</xsl:if><xsl:text>"""

from typing import List, Dict, Tuple, Optional, Any
from schema.errors import MpSchemaError
from data_classes.errors import DcError, DataClassLoadingError
from schema.gt.enum.mp_status import MpStatus</xsl:text>

<xsl:text>
from data_classes.</xsl:text>             <xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(DataClass,'.','_')"  />
  </xsl:call-template><xsl:text> import </xsl:text><xsl:value-of select="DataClassCamel"/>


<xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and (FromDataClass='true')]">
<xsl:text>
from data_classes.</xsl:text>             <xsl:call-template name="python-case">
    <xsl:with-param name="camel-case-text" select="translate(DataClassCamel,'.','_')"  />
  </xsl:call-template><xsl:text> import </xsl:text><xsl:value-of select="DataClassCamel"/>
</xsl:for-each>

<xsl:text>
from schema.gt.gnr.</xsl:text><xsl:value-of select="NtClass"/>
<xsl:text>.</xsl:text><xsl:value-of select="translate(Alias,'.','_')"/>
<xsl:text> import </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="KafkaAlias" />
</xsl:call-template>




<xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and (TypeIsNtClass='true')]">
    <xsl:variable name="snake-param">
       <xsl:call-template name="python-case">
           <xsl:with-param name="camel-case-text" select="Value"  />
       </xsl:call-template>
</xsl:variable>
        <xsl:text>
from schema.gt.gnr.</xsl:text><xsl:value-of select="NtClass"/><xsl:text>.</xsl:text>
<xsl:value-of select="translate(SubMessageFormatAlias,'.','_')"/><xsl:text>_maker import \
</xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
    <xsl:text>_Maker, </xsl:text>
<xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
</xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id)  and (normalize-space(FormatIsStringSet)='true')]">
        <xsl:text>
from enums.</xsl:text>
             <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="translate(FormatAlias,'.','_')"  />
          </xsl:call-template>

        <xsl:text> import </xsl:text><xsl:value-of select="translate(FormatAlias,'.','_')"/>
    </xsl:for-each>


    <xsl:text>
    
    
class </xsl:text><xsl:value-of select="$nt-name"/><xsl:text>_Maker():
    mp_alias = '</xsl:text><xsl:value-of select="Alias"/><xsl:text>'
    mp_status = MpStatus.</xsl:text><xsl:value-of select="translate(Status,$lcletters, $ucletters)"/><xsl:text>.value

    @classmethod
    def camel_dict_to_schema_type(cls, d:dict) -> </xsl:text>
    <xsl:if test="(IsNamedTuple='true')">
    <xsl:value-of select="$nt-name"/>
    </xsl:if>
    <xsl:if test="not(IsNamedTuple='true')">
    <xsl:text>Payload</xsl:text>
    </xsl:if>
    <xsl:text>:
        if 'MpAlias' not in d.keys():
            d['MpAlias'] = '</xsl:text>
            <xsl:value-of select="$mp-schema-alias"/>
            <xsl:text>'</xsl:text>

        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and (TypeIsNtClass = 'true')]">
        <xsl:text>
        if '</xsl:text><xsl:value-of select="Value"/><xsl:text>' not in d.keys():</xsl:text>
        <xsl:if test="not (IsRequired = 'true')">
            <xsl:text>
            d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] = None
        else:</xsl:text>
            <xsl:if test="not (IsList='true')">
                <xsl:text>
            Gt</xsl:text><xsl:value-of select="Value"/>
                <xsl:text> = </xsl:text>
                <xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
    <xsl:text>_Maker.camel_dict_to_schema_type(d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"])</xsl:text>

            </xsl:if>
            <xsl:if test= "(IsList='true')">
            <xsl:text>
            Gt</xsl:text><xsl:value-of select="Value"/><xsl:text> = []
            if not isinstance(d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"], list):
                raise MpSchemaError('d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] must be a list!!')
            for elt in d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]:
                Gt</xsl:text><xsl:value-of select="Value"/><xsl:text>.append(</xsl:text>
                <xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
                <xsl:text>_Maker.camel_dict_to_schema_type(elt))</xsl:text>
            </xsl:if>
        </xsl:if>
        <xsl:if test="IsRequired = 'true'">
            <xsl:text>
            raise MpSchemaError("Missing required '</xsl:text><xsl:value-of select="Value"/><xsl:text>' in </xsl:text><xsl:value-of select="$mp-schema-alias"/><xsl:text> message")</xsl:text>
        <xsl:if test="not (IsList='true')">
            <xsl:text>
        Gt</xsl:text><xsl:value-of select="Value"/>
            <xsl:text> = </xsl:text>
            <xsl:call-template name="nt-case">
    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
</xsl:call-template>
            <xsl:text>_Maker.camel_dict_to_schema_type(d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"])</xsl:text>

        </xsl:if>
        <xsl:if test= "(IsList='true')">
        <xsl:text>
        Gt</xsl:text><xsl:value-of select="Value"/><xsl:text> = []
        if not isinstance(d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"], list):
            raise MpSchemaError('d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] must be a list!!')
        for elt in d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]:
            Gt</xsl:text><xsl:value-of select="Value"/><xsl:text>.append(</xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
            </xsl:call-template>
            <xsl:text>_Maker.camel_dict_to_schema_type(elt))</xsl:text>
        </xsl:if>
        </xsl:if>
        </xsl:for-each>
        
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and not (IsRequired='true') and not (TypeIsNtClass = 'true')]">

        <xsl:text>
        if "</xsl:text><xsl:value-of select="Value"/><xsl:text>" not in d.keys():
            d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] = None</xsl:text>
        <xsl:if test="(PrimitiveType='Number') and not (IsList='true')">
        <xsl:text> 
        elif not d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] is None:
            d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] = float(d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"])</xsl:text>
        </xsl:if>
        </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and not (TypeIsNtClass = 'true') and (IsList='true') and (PrimitiveType='Number')]">
        <xsl:text>
        list_as_floats = []
        if not isinstance(d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"], list):
            raise MpSchemaError('d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] must be a list!!')
        for elt in d["</xsl:text> <xsl:value-of select="Value"/><xsl:text>"]:
            try:
                list_as_floats.append(float(elt))
            except ValueError:
                pass # This will get caught in is_valid() check below
        d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"] = list_as_floats</xsl:text>
        </xsl:for-each>
        <xsl:if test="not(AlwaysSimulated = 'true')">
        <xsl:text>
        if "WorldInstanceAlias" not in d.keys():
            d["WorldInstanceAlias"] = None</xsl:text>
        </xsl:if>
        <xsl:text>
        p = </xsl:text>
        <xsl:if test="(IsNamedTuple='true')">
        <xsl:value-of select="$nt-name"/>
        </xsl:if>
        <xsl:if test="not (IsNamedTuple='true')">
        <xsl:text>Payload</xsl:text>
        </xsl:if>
        <xsl:text>(MpAlias=d["MpAlias"]</xsl:text>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and not (TypeIsNtClass = 'true')]">
        <xsl:if test="TypeInPayload = 'Number' and (IsRequired='true')">
                    <xsl:text>,
                        </xsl:text><xsl:value-of select="Value"/><xsl:text>=float(d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"])</xsl:text>
        </xsl:if>
        <xsl:if test="not (TypeInPayload = 'Number') or not (IsRequired='true')">
                    <xsl:text>,
                        </xsl:text><xsl:value-of select="Value"/><xsl:text>=d["</xsl:text><xsl:value-of select="Value"/><xsl:text>"]</xsl:text>
        </xsl:if>
        </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and (TypeIsNtClass = 'true')]">
        <xsl:text>,
                        </xsl:text><xsl:value-of select="Value"/><xsl:text>=Gt</xsl:text><xsl:value-of select="Value"/><xsl:text>
        </xsl:text>
        </xsl:for-each> <xsl:if test="not (IsNamedTuple='true')"><xsl:text>,
                        WorldInstanceAlias=d["WorldInstanceAlias"]</xsl:text>
        </xsl:if><xsl:text>)
        is_valid, errors = p.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        return p </xsl:text>
    <xsl:if test="(FromDataClass='true')">
        <xsl:text>

    @classmethod
    def data_class_to_schema_type(cls,dc:</xsl:text><xsl:value-of select="DataClassCamel"/><xsl:text>) -> </xsl:text>
    <xsl:value-of select="$nt-name"/>
    <xsl:text>:
        if dc is None:
            return None
        candidate = </xsl:text><xsl:value-of select="$nt-name"/>
        <xsl:text>(MpAlias='</xsl:text><xsl:value-of select="$mp-schema-alias"/><xsl:text>'</xsl:text>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) ]">
        <xsl:if test="(TypeInPayload = 'Number') and (IsRequired = 'true')">
            <xsl:text>,
                        </xsl:text><xsl:value-of select="Value"/><xsl:text>=float(dc.</xsl:text> <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template><xsl:text>)</xsl:text>
        </xsl:if>
        <xsl:if test="not (IsRequired = 'true') or not (TypeInPayload = 'Number')">
    
    
                    <xsl:text>,
                        </xsl:text><xsl:value-of select="Value"/>
                        <xsl:text>=dc.</xsl:text> 
                        <xsl:call-template name="python-case">
                            <xsl:with-param name="camel-case-text" select="Value"  />
                        </xsl:call-template>
                </xsl:if>
        </xsl:for-each>
        <xsl:text>)
        is_valid, errors = candidate.is_valid()
        if not is_valid:
            raise MpSchemaError(errors)
        else:
            return candidate
    
    @classmethod
    def schema_type_to_data_class(cls,p:</xsl:text><xsl:value-of select="$nt-name"/><xsl:text>) -> </xsl:text>
    <xsl:value-of select="DataClassCamel"/>
    <xsl:text>:
        if p is None:
            return None
        snake_dict = {}</xsl:text>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) ]">
        <xsl:text>
        snake_dict['</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>']=p.</xsl:text><xsl:value-of select="Value"/>
        </xsl:for-each>
        <xsl:text>
        if snake_dict['</xsl:text><xsl:value-of select="DataClass"/> <xsl:text>_id'] in </xsl:text>
        <xsl:value-of select="DataClassCamel"/><xsl:text>.by_id.keys():
            </xsl:text><xsl:value-of select="DataClass"/> <xsl:text> = </xsl:text>
            <xsl:value-of select="DataClassCamel"/><xsl:text>.by_id[snake_dict['</xsl:text><xsl:value-of select="DataClass"/> <xsl:text>_id']]
            try:
                </xsl:text><xsl:value-of select="DataClass"/> <xsl:text>.check_update_consistency(snake_dict)
            except DcError or DataClassLoadingError as err:
                print(f'Not updating or returning </xsl:text><xsl:value-of select="DataClassCamel"/><xsl:text>: {err}')
                return None
            except KeyError as err:
                print(f'Not updating or returning </xsl:text><xsl:value-of select="DataClassCamel"/><xsl:text>: {err}')
                return None

            for key, value in snake_dict.items():
                if hasattr(</xsl:text><xsl:value-of select="DataClass"/> <xsl:text>, key):
                    setattr(</xsl:text><xsl:value-of select="DataClass"/> <xsl:text>, key, value)
        else:
            </xsl:text><xsl:value-of select="DataClass"/> <xsl:text> = </xsl:text><xsl:value-of select="DataClassCamel"/><xsl:text>(**snake_dict)

        return </xsl:text><xsl:value-of select="DataClass"/>

    </xsl:if><xsl:text>

    @classmethod
    def type_is_valid(cls, object_as_dict: Dict[str, Any]) -> Tuple[bool, Optional[List[str]]]:
        try:
            p = cls.camel_dict_to_schema_type(object_as_dict)
        except MpSchemaError as e:
            errors = [e]
            return False, errors
        return p.is_valid()

    def __init__(self</xsl:text>
            <xsl:if test="not($mp-schema-type='MessageSubset')">
            <xsl:text>, agent</xsl:text></xsl:if>
         <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true']">
                <xsl:if test="Value='ToGNodeAlias' ">
              <xsl:text>,
                 to_g_node_alias: str</xsl:text>
             </xsl:if>
         </xsl:for-each>
         <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true']">
                <xsl:if test="Value='AboutGNodeAlias' ">
              <xsl:text>,
                 about_g_node_alias: str</xsl:text>
             </xsl:if>
         </xsl:for-each>
          <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired='true') and not (IsList='true') and not (normalize-space(FormatIsStringSet)='true') and not (TypeIsNtClass='true')]">
             <xsl:variable name="snake-param">
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template>
             </xsl:variable>
             <xsl:if test="Value='StartYearUtc' ">
                <xsl:text>,
                 start_utc: datetime.datetime</xsl:text>
            </xsl:if>
            <xsl:if test="not(Value='StartMinuteUtc') and not(Value='StartHourUtc') and not(Value='StartDayUtc') and not(Value='StartMonthUtc') and not(Value='StartYearUtc')">                  
             <xsl:text>,
                 </xsl:text>
             <xsl:value-of select="$snake-param"/>
             <xsl:text>: </xsl:text>
             <xsl:call-template name="python-type">
                <xsl:with-param name="gw-type" select="TypeInPayload"/>
            </xsl:call-template>
            </xsl:if>
        </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired='true') and (IsList='true') and not (TypeIsNtClass='true')]">
        <xsl:variable name="snake-param">
           <xsl:call-template name="python-case">
               <xsl:with-param name="camel-case-text" select="Value"  />
           </xsl:call-template>
        </xsl:variable>
        <xsl:text>,
                 </xsl:text>
        <xsl:value-of select="$snake-param"/>
        <xsl:text>: List[</xsl:text>
        <xsl:call-template name="python-type">
           <xsl:with-param name="gw-type" select="PrimitiveType"/>
       </xsl:call-template><xsl:text>]</xsl:text>
   </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired='true') and not (IsList='true') and (TypeIsNtClass='true') and (FromDataClass='true')]">
        <xsl:variable name="snake-param">
           <xsl:call-template name="python-case">
               <xsl:with-param name="camel-case-text" select="Value"  />
           </xsl:call-template>
        </xsl:variable>
            <xsl:text>,
                 </xsl:text>
            <xsl:value-of select="$snake-param"/>
            <xsl:text>: </xsl:text>
            <xsl:value-of select = "DataClassCamel"/>
        </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired='true') and not (IsList='true') and (TypeIsNtClass='true') and not (FromDataClass='true')]">
        <xsl:variable name="snake-param">
           <xsl:call-template name="python-case">
               <xsl:with-param name="camel-case-text" select="Value"  />
           </xsl:call-template>
        </xsl:variable>
            <xsl:text>,
                 </xsl:text>
            <xsl:value-of select="$snake-param"/>
            <xsl:text>: </xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
            </xsl:call-template>
        </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired='true') and (IsList='true') and (TypeIsNtClass='true') and (FromDataClass='true')]">
        <xsl:variable name="snake-param">
           <xsl:call-template name="python-case">
               <xsl:with-param name="camel-case-text" select="ValueLocal"  />
           </xsl:call-template>
        </xsl:variable>
            <xsl:text>,
                 </xsl:text>
            <xsl:value-of select="$snake-param"/>
            <xsl:text>: List[</xsl:text>
            <xsl:value-of select = "DataClassCamel"/>
            <xsl:text>]</xsl:text>
        </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsRequired='true') and (IsList='true') and (TypeIsNtClass='true') and not (FromDataClass='true')]">
        <xsl:variable name="snake-param">
           <xsl:call-template name="python-case">
               <xsl:with-param name="camel-case-text" select="Value"  />
           </xsl:call-template>
        </xsl:variable>
            <xsl:text>,
                 </xsl:text>
            <xsl:value-of select="$snake-param"/>
            <xsl:text>: List[</xsl:text>
            <xsl:call-template name="nt-case">
                <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
            </xsl:call-template><xsl:text>]</xsl:text>
        </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (normalize-space(FormatIsStringSet)='true')]">
        <xsl:variable name="snake-param">
           <xsl:call-template name="python-case">
               <xsl:with-param name="camel-case-text" select="Value"  />
           </xsl:call-template>
        </xsl:variable>
        <xsl:text>,
                 </xsl:text><xsl:value-of select="$snake-param"/><xsl:text>=</xsl:text>
            <xsl:value-of select="translate(FormatAlias,'.','_')"/><xsl:text>.</xsl:text>
            <xsl:call-template name="upper-python-case">
                <xsl:with-param name="camel-case-text" select="DefaultValue" />
            </xsl:call-template><xsl:text>.value</xsl:text>
         </xsl:for-each>
         <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired='true') and not (IsList='true') and not (normalize-space(FormatIsStringSet)='true') and not (TypeIsNtClass='true')]">
         <xsl:variable name="snake-param">
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
         </xsl:variable>
         <xsl:text>,
                 </xsl:text>
         <xsl:value-of select="$snake-param"/>
         <xsl:text>: Optional[</xsl:text>
         <xsl:call-template name="python-type">
            <xsl:with-param name="gw-type" select="TypeInPayload"/>
        </xsl:call-template><xsl:text>] = None </xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired='true') and (IsList='true') and not (TypeIsNtClass='true')]">
    <xsl:variable name="snake-param">
       <xsl:call-template name="python-case">
           <xsl:with-param name="camel-case-text" select="Value"  />
       </xsl:call-template>
    </xsl:variable>
    <xsl:text>,
                 </xsl:text>
    <xsl:value-of select="$snake-param"/>
    <xsl:text>: Optional[List[</xsl:text>
    <xsl:call-template name="python-type">
       <xsl:with-param name="gw-type" select="TypeLocal"/>
   </xsl:call-template><xsl:text>]] = None</xsl:text>
</xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired='true') and not (IsList='true') and (TypeIsNtClass='true') and (FromDataClass='true')]">
    <xsl:variable name="snake-param">
       <xsl:call-template name="python-case">
           <xsl:with-param name="camel-case-text" select="Value"  />
       </xsl:call-template>
    </xsl:variable>
        <xsl:text>,
                 </xsl:text>
        <xsl:value-of select="$snake-param"/>
        <xsl:text>: Optional[</xsl:text>
        <xsl:value-of select = "DataClassCamel"/><xsl:text>] = None</xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired='true') and not (IsList='true') and (TypeIsNtClass='true') and not (FromDataClass='true')]">
    <xsl:variable name="snake-param">
       <xsl:call-template name="python-case">
           <xsl:with-param name="camel-case-text" select="Value"  />
       </xsl:call-template>
    </xsl:variable>
        <xsl:text>,
                 </xsl:text>
        <xsl:value-of select="$snake-param"/>
        <xsl:text>: Optional[</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
        </xsl:call-template><xsl:text>] = None</xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired='true') and (IsList='true') and (TypeIsNtClass='true') and (FromDataClass='true')]">
    <xsl:variable name="snake-param">
       <xsl:call-template name="python-case">
           <xsl:with-param name="camel-case-text" select="ValueLocal"  />
       </xsl:call-template>
    </xsl:variable>
        <xsl:text>,
                 </xsl:text>
        <xsl:value-of select="$snake-param"/>
        <xsl:text>: Optional[List[</xsl:text>
        <xsl:value-of select = "DataClassCamel"/>
        <xsl:text>]] = None</xsl:text>
    </xsl:for-each>
    <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (IsRequired='true') and (IsList='true') and (TypeIsNtClass='true') and not (FromDataClass='true')]">
    <xsl:variable name="snake-param">
       <xsl:call-template name="python-case">
           <xsl:with-param name="camel-case-text" select="Value"  />
       </xsl:call-template>
    </xsl:variable>
        <xsl:text>,
                 </xsl:text>
        <xsl:value-of select="$snake-param"/>
        <xsl:text>: Optional[List[</xsl:text>
        <xsl:call-template name="nt-case">
            <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
        </xsl:call-template><xsl:text>]] = None</xsl:text>
    </xsl:for-each>
                            <xsl:text>):</xsl:text>
        <xsl:if test="not($mp-schema-type='MessageSubset')">
        <xsl:text>
        super(</xsl:text><xsl:value-of select="$class-name"/>
                            <xsl:text>, self).__init__(routing_key_base='</xsl:text><xsl:value-of select="$routing-key-base"/><xsl:text>', agent=agent)</xsl:text>
        </xsl:if>
        <xsl:text>
        self.errors = []</xsl:text>

        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (IsList='true') and (TypeIsNtClass='true') and (FromDataClass='true')]">
        <xsl:text>
        if not isinstance(</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="ValueLocal"  />
        </xsl:call-template>
        <xsl:text>, list):
            raise MpSchemaError('</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="ValueLocal"  />
            </xsl:call-template>
            <xsl:text> must be a list!!')
        gt_</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="ValueLocal"  />
        </xsl:call-template>
        <xsl:text> = []
        for elt in </xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="ValueLocal"  />
        </xsl:call-template>
        <xsl:text>:
            gt_</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="ValueLocal"  />
            </xsl:call-template>
            <xsl:text>.append(</xsl:text> 
            <xsl:call-template name="message-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                </xsl:call-template>
           <xsl:text>.payload_from_data_class(elt))</xsl:text>
        </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and not(IsList='true') and (Type='Number')]">
        <xsl:text>
        try:
            </xsl:text>
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template><xsl:text> = float(</xsl:text>
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template>
            <xsl:text>)
        except ValueError:
            pass # This will get caught in is_valid() check below</xsl:text>
        </xsl:for-each>
        <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and (IsList='true') and (Type='Number')]">
        <xsl:text>
        if not isinstance(</xsl:text> <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template>
         <xsl:text>,list):
             raise MpSchemaError(f"</xsl:text> <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
             <xsl:text> must be a list!!")
        try:
            tmp_</xsl:text>
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template><xsl:text> = []
            for elt in </xsl:text> <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template>
             <xsl:text>:
                tmp_</xsl:text> 
                <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template>
                <xsl:text>.append(float(elt))
            </xsl:text><xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="Value"  />
            </xsl:call-template><xsl:text> = tmp_</xsl:text>
        <xsl:call-template name="python-case">
            <xsl:with-param name="camel-case-text" select="Value"  />
        </xsl:call-template><xsl:text>
        except ValueError:
            pass # This will get caught in is_valid() check below</xsl:text>
        </xsl:for-each>
        <xsl:text>

        t = </xsl:text>
        <xsl:value-of select="$nt-name"/>
        <xsl:text>(MpAlias=</xsl:text><xsl:value-of select="$nt-name"/><xsl:text>_maker.mp_alias</xsl:text>
        <xsl:if test="not (IsNamedTuple='true')"><xsl:text>,
                    WorldInstanceAlias=world_instance_alias</xsl:text>
        </xsl:if>
            <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true']">
                <xsl:if test="Value='FromGNodeAlias' ">
              <xsl:text>,
                    FromGNodeAlias=from_g_node_alias</xsl:text>
             </xsl:if>
            </xsl:for-each>
            <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true']">
                <xsl:if test="Value='FromGNodeInstanceId' ">
              <xsl:text>,
                    FromGNodeInstanceId=from_g_node_instance_id</xsl:text>
             </xsl:if>
            </xsl:for-each>
            <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true']">
                <xsl:if test="Value='ToGNodeAlias' ">
              <xsl:text>,
                    ToGNodeAlias=to_g_node_alias</xsl:text>
             </xsl:if>
            </xsl:for-each>
            <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true']">
                <xsl:if test="Value='AboutGNodeAlias' ">
              <xsl:text>,
                    AboutGNodeAlias=about_g_node_alias</xsl:text>
             </xsl:if>
            </xsl:for-each>
            <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='true']">
            </xsl:for-each>
             <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and not (FromDataClass='true')]">
                <xsl:text>,
                    </xsl:text>
             <xsl:value-of select="Value"/><xsl:text>=</xsl:text>
                 <xsl:call-template name="python-case">
                    <xsl:with-param name="camel-case-text" select="Value"  />
                </xsl:call-template>
             </xsl:for-each>
             <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (FromDataClass='true') and not (IsList='true')]">
                <xsl:text>,
                    </xsl:text>
             <xsl:value-of select="Value"/><xsl:text>=</xsl:text>
             <xsl:call-template name="message-case">
                    <xsl:with-param name="mp-schema-text" select="SubMessageFormatAlias" />
                </xsl:call-template><xsl:text>.payload_from_data_class(</xsl:text>
                  <xsl:call-template name="python-case">
                     <xsl:with-param name="camel-case-text" select="Value"  />
                 </xsl:call-template><xsl:text>)</xsl:text>
              </xsl:for-each>
              <xsl:for-each select="$airtable//MpMessagePayloadProperties/MpMessagePayloadProperty[(MpSchema = $mp-schema-id) and normalize-space(InPreamble)='false' and (FromDataClass='true') and(IsList='true')]">
              <xsl:text>,
                    </xsl:text>
              <xsl:value-of select="Value"/><xsl:text>=gt_</xsl:text>
            <xsl:call-template name="python-case">
                <xsl:with-param name="camel-case-text" select="ValueLocal"  />
            </xsl:call-template>
               </xsl:for-each>
            <xsl:text>)

        is_valid, errors = t.is_valid()
        if is_valid is False:
            raise MpSchemaError(f"Failed to create payload due to these errors: {errors}")</xsl:text>
                            <xsl:text>
        self.type = t

</xsl:text>




                        </xsl:element>
                     </FileSetFile>
                </xsl:for-each>

            </FileSetFiles>
        </FileSet>
    </xsl:template>



</xsl:stylesheet>