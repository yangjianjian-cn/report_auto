#!/usr/bin/env python
# @desc : 
__coding__ = "utf-8"
__author__ = "xxx team"

from pojo.Iaapp1_level2_ErrorDetection import ErrorDetection
from pojo.Iaapp1_level1_PinData import PinData
from pojo.Iaapp1_level3_debouncing_healing import debouncing_healing
from pojo.Iaapp1_level4_substitute_value_reaction import substitute_value_reaction

i_a_app1_level1_data = PinData(
        column1=' ',
        pin_no='61',
        pin='I_A_APP1',
        short_name='APP_uRaw1',
        long_name='Accelerator pedal position 1',
        information_hints=' ',
        device_doc='APP_DD1',
        level1=' ',
        checked_values='APP_uRaw1',
        preparation=' ',
        stimulation=' ',
        measurements='APP_uRaw1unLim'
    )
i_a_app1_level1_attribute = ['column1', 'pin_no', 'pin', 'short_name', 'long_name', 'information_hints', 'device_doc',
                          'level1',
                          'checked_values',
                          'preparation', 'stimulation', 'measurements']  # , 'result'

# result=level2
i_a_app1_level2_data = ErrorDetection(
    level2=" ",
    checked_errors="SRCH, SRCL",
    preparation="APP_uRaw1SRCHigh_C\nAPP_uRaw1SRCLow_C",
    stimulation=" ",
    measurements="DFC_st.DFC_SRCHighAPP1\nDFC_st.DFC_SRCLowAPP1",
)
i_a_app1_level2_attribute = ['level2', 'checked_errors', 'preparation', 'stimulation', 'measurements']  # 'result'


i_a_app1_level3_data = debouncing_healing(
    level3=" ",
    checked="SRCH, SRCL",
    preparation="DDRC_DurDeb.APP_tiSRCHighDebDef_C\nDDRC_DurDeb.APP_tiSRCHighDebOk_C\nDDRC_DurDeb.APP_tiSRCLowDebDef_C\nDDRC_DurDeb.APP_tiSRCLowDebOk_C",
    stimulation=" ",
    measurements="DFC_st.DFC_SRCHighAPP1\nDFC_st.DFC_SRCLowAPP1"
)
i_a_app1_level3_attribute =['level3', 'checked', 'preparation', 'stimulation', 'measurements']  # 'result'


i_a_app1_level4_data = substitute_value_reaction(
    level4=" ",
    error_substitute="SRCH, SRCL",
    preparation="APP_uRaw1Def_C",
    stimulation=" ",
    measurements="APP_uRaw1",
)
i_a_app1_level4_attribute =['level4', 'error_substitute', 'preparation', 'stimulation', 'measurements']  # 'result'
