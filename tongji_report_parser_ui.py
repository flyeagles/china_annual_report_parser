import streamlit as st
import mysql.connector
import argparse
from io import StringIO
from bs4 import BeautifulSoup

from docx_parser_converter.docx_to_txt.docx_to_txt_converter import DocxToTxtConverter
#from docx_parser_converter.docx_parsers.utils import read_binary_from_file_path


def get_field_names() -> list:
    return [
        'gdp',
        '第一产业增加值',
        '第二产业增加值',
        '第三产业增加值',
        '人均GDP',
        '一般公共预算收入',
        '税收收入',
        '一般公共预算支出',
        '工业增加值',
        '建筑业总产值',
        '建筑业增加值',
        '房屋建筑竣工面积',
        '商品房销售面积',
        '商品房销售额',
        '社会消费品零售总额',
        '城镇消费品零售额',
        '乡村消费品零售额',
        '餐饮收入',
        '外贸进出口总额',
        '出口',
        '进口',
        '实际利用外资',
        '公路旅客运输量',
        '公路通车里程',
        '汽车',
        '摩托车',
        '旅游总收入',
        '国内外旅游人数',
        '国内旅游收入',
        '国内旅游人数',
        '金融机构人民币各项存款余额',
        '住户存款',
        '非金融企业',
        '金融机构人民币各项贷款余额',
        '住户贷款',
        '各类学校',
        '在校生',
        '教职工',
        '专任教师',
        '幼儿园',
        '幼儿',
        '小学',
        '小学学生',
        '普通中学',
        '中学生',
        '初中在校生',
        '高中在校生',
        '常住人口',
        '城镇化率',
        '人口出生率',
        '人口死亡率',
        '自然增长率',
        '户籍人口',
        '农业人口',
        '非农业人口',
        '城镇常住居民人均可支配收入',
        '农村常住居民人均可支配收入'
    ]

def get_pattern_for_field(field:str) -> list:
    match field:
        case 'gdp':   return ['[^位对动元占均]GDP(?!生产)', '地区生产总值', '县内生产总值', '市生产总值', '国内生产总值']
        case '第一产业增加值':  return ['第一产业增加值', '第一产业实现增加值', '一产业']
        case '第二产业增加值':  return ['第二产业增加值', '第二产业实现增加值', '二产业']
        case '第三产业增加值': return ['第三产业增加值', '第三产业实现增加值', '第三产业.*?实现增加值', '三产业']
        case '人均GDP': return ['人均(?:地区)?生产总值', '人均GDP', '人均国内生产总值']
        case '一般公共预算收入': return ['一般公共预算收入', '地方公共财政预算收入', '公共财政预算收入', '[^占]财政总收入', '一般预算收入']
        case '税收收入': return ['税收收入(?!占)']
        case '一般公共预算支出': return ['一般公共预算支出', '地方公共财政预算支出', '一般公共财政预算支出', '公共(?:财政)?预算支出',
                                         '财政总?支出(?!的)', '一般预算支出']
        case '工业增加值': return ['[^模业]工业增加值(?![同占比的增对])', '工业实现增加值']
        case '建筑业总产值': return ['建筑业总产值', '建筑业企业实现总产值', '建筑企?业实现总产值']
        case '建筑业增加值': return ['建筑业增加值']
        case '房屋建筑竣工面积': return ['房屋(?:建筑)?竣工面积']
        case '商品房销售面积': return ['商品房屋?销售面积', '房产销售面积']
        case '商品房销售额': return ['商品房销售额', '房地产销售额', '房产销售.{1,12}完成销售额']
        case '社会消费品零售总额': return ['社会消费品零售总?额', '社会商品零售总额']
        case '城镇消费品零售额': return ['城[市镇].{0,3}消费.{0,2}零售.{0,2}额', '城镇零售额']
        case '乡村消费品零售额': return ['[乡农]村.{0,3}消费.{0,2}零售.{0,2}额', '乡村零售额', '县及县以下消费品零售额']
        case '餐饮收入':  return ['餐饮收入', '餐饮业营业额', '餐饮业零售额', '餐饮消费额', '餐饮业']
        case '外贸进出口总额': return ['外贸进出口总额', '进出口贸易总额', '进出口总额']
        case '出口':  return ['[^进]出口']
        case '进口':  return ['进口']
        case '实际利用外资':  return ['实际利用外资(?!项目)', '实际利用外商直接投资', '实际到位外资', '直接利用外资', '外商直接投资']
        case '公路旅客运输量':  return ['公路旅客运输量', '交通系统客运量', '旅客运输总量']
        case '公路通车里程': return ['公路通车里程', '通车里程']
        case '汽车': return ['机动车.*?汽车', '汽车保有量', '机动车保有量']
        case '摩托车': return ['摩托车']
        case '旅游总收入': return ['旅游总收入', '旅游业总收入', '实现旅游收入', '旅游综合收入','旅游社会总收入']
        case '国内外旅游人数': return ['国内外旅游人数', '国内外旅游者', '共接待旅游者', '接待境内外游客', '接待游客']
        case '国内旅游收入':  return ['国内旅游收入']
        case '国内旅游人数': return ['国内游客']
        case '金融机构人民币各项存款余额': return ['金融机构人民币各项存款余额', '金融机构人民币存款余额', '金融机构各项存款余额', '金融机构存款余额',
                                                   '各项存款余额', '各项本外币存款余额']
        case '住户存款':  return ['住户存款', '居民储蓄存款', '个人存款余额']
        case '非金融企业':  return ['非金融企业存款']
        case '金融机构人民币各项贷款余额': return ['金融机构人民币各项贷款余额', '金融机构人民币贷款余额', '金融机构各项贷款余额',
                                                   '各项贷款余额', '本外币贷款余额']
        case '住户贷款':  return ['住户贷款']
        case '各类学校': return ['各类学校']
        case '在校生':  return ['在校中小学生', '[^中学]在校生', '在校学生']
        case '教职工': return ['教职工', '教师总人数']
        case '专任教师': return ['专任教师']
        case '幼儿园': return ['幼儿园(?!在)']
        case '幼儿': return ['在园.*?幼儿']
        case '小学': return ['小学(?![招适学毕生在被])']
        case '小学学生': return ['在校学生总人数.{1,10}其中.{1,21}小学', '[^中]小学.{0,12}?在校学?生', '[^中]小学生',
                                 '普通小学.{0,16}在校学?生']
        case '普通中学': return ['普通中学']
        case '中学生': return ['普通中学.{0,8}在校学?生', '在校学生总人数.{1,12}普通中学']
        case '初中在校生': return ['初中.{0,12}在校学?生', '初中生', '初中学校.{1,15}在校学?生']
        case '高中在校生': return ['高中.{0,12}?在校学?生', '高中生', '高中.{1,13}在校学?生']
        case '常住人口':  return  ['[^按]常住人口', '[^过]全市总人口']
        case '城镇化率': return ['城镇化率', '城镇人口.*?占户籍人口比重为']
        case '人口出生率':  return ['人口出生率', '出生率']
        case '人口死亡率': return ['[^故车妇儿童]死亡率']
        case '自然增长率': return ['自然增长率(?!继续)']
        case '户籍人口': return ['[^占区]户籍总?人口', '总人口(?![同的])']
        case '农业人口': return ['农业人口', '农村人口']
        case '非农业人口': return ['非农业人口', '城镇人口']
        case '城镇常住居民人均可支配收入': return ['城[市镇](?:常住)?居民年?人均可支配收入', '城[市镇]居民人平可支配收入',
                                                   '城镇居民可支配收入']
        case '农村常住居民人均可支配收入': return ['农村(?:常住)?居民人均可支配收入', '农村居民年?人均纯收入', '农村居民人平可支配收入',
                                                '农民人均纯收入(?!增)', '农民人均可支配收入']
        case _: return ''

    return ''

import re
def parse_report(text: str) -> list:
    result = []
    loc_fields = get_field_names()
    for field in loc_fields:
        pat_list = get_pattern_for_field(field)
        found = False
        pattern_len = 1000
        unit = None
        val_str = None
        matched = None
        for pat in pat_list:
            pattern = '(' + pat + r')[^\d\r\n]{0,20}?([\d\-][\d\.\- ]+)\s*([十百千万亿]*)'
            mat = re.search(pattern, text)
            if mat:
                print(pattern, mat.group(1), mat.group(2), mat.group(3))
                if len(mat.group(1)) < pattern_len:
                    pattern_len = len(mat.group(1))
                    unit = mat.group(3)
                    val_str = mat.group(2)
                    matched = mat.group(1)
                    found = True

        if found:
            val_str = val_str.replace(' ', '')
            val = float(val_str)
            match unit:
                case '千':
                    factor = 1000
                case '万':
                    factor = 10000
                case '十万':
                    factor = 100000
                case '百万':
                    factor = 1000000
                case '千万':
                    factor = 10000000
                case '亿' | '亿万':
                    factor = 100000000
                case '十亿':
                    factor = 1000000000
                case _:
                    factor = 1
            val = round(val*factor, 2)
            result.append((field, val, matched))
        else:
            result.append((field, -1, ''))

    return result

class text_field:
    def __init__(self, label, columns=None, **input_params):
        self.label = label
        self.columns = columns if columns else [2, 2, 2, 1]
        self.need_edit = False
        self.input_params = input_params
        self.use_editor = False
        self.val = None


    def render(self, val, hint:str):
        c1, c2, c3, c4 = st.columns(self.columns)
        # Display field name with some alignment
        #c1.markdown("#####")
        c1.markdown(self.label)
        c3.markdown(hint)
        need_edit = c4.button('Edit', key=self.label+'button')
        if not self.need_edit:
            self.need_edit = need_edit
            if need_edit:
                self.use_editor = True

        if self.use_editor:
            # Sets a default key parameter to avoid duplicate key errors
            self.input_params.setdefault("key", self.label)

            print(f'{self.label} row is clicked.')
            # Forward text input parameters
            self.val = c2.number_input(" ", value=self.val, **self.input_params)
        else:
            self.val = val
            c2.markdown(f'{self.val:,}')

        return self.val


# @st.cache_data
def get_sql_connection(pwd:str):
    cnx = mysql.connector.connect(
        user='yluo',
        password=pwd,
        host='127.0.0.1',
        port=3306,
        database='city_eco',
        charset='utf8mb4',
        collation='utf8mb4_unicode_ci'
    )
    return cnx

@st.dialog("MySQL Eror")
def SQLFail(reason):
    st.write(f"MySQL got error: {reason}")

@st.dialog("MySQL Success")
def SQLSuccess():
    st.write(f"MySQL insertion succeeds.")
def show_page(pwd:str):
    # Set the mode of the app to "wide"
    st.set_page_config(page_title="统计报告分析", page_icon=None, layout="wide")

    # Create two columns, one for the text input and another for the 10 text fields
    col1, col2 = st.columns([7, 4])

    changed = False
    data_year = 2023
    with col1:
        uploaded_file = st.file_uploader("打开统计报告（HTML or txt）")
        if uploaded_file is not None:
            filename = uploaded_file.name

            if '.docx' in filename:
                converter = DocxToTxtConverter(uploaded_file.getvalue(), use_default_values=True)
                string_data = converter.convert_to_txt(indent=True)
            else:
                # To convert to a string based IO:
                try:
                    stringio = StringIO(uploaded_file.getvalue().decode("utf-8"))
                except UnicodeDecodeError as err:
                    stringio = StringIO(uploaded_file.getvalue().decode("gbk"))

                # To read file as string:
                string_data = stringio.read()
                if '.htm' in filename:
                    string_data = re.sub(r'</?span.*?>\n?', '', string_data, flags=re.IGNORECASE)
                    string_data = re.sub(r'</?font.*?>\n?', '', string_data, flags=re.IGNORECASE)
                    string_data = re.sub(r'\n', '', string_data)
                    string_data = re.sub(r'</p>', '</p>\n', string_data)
                    #print(string_data)
                    soup = BeautifulSoup(string_data)
                    string_data = soup.get_text(separator=' ')
                    #print(string_data)
                    string_data = re.sub(r'\n+', '\n', string_data)
                    string_data = re.sub(r'  +', ' ', string_data)

            string_data = re.sub(r'\[\d*\]', '', string_data)

            year_pat = re.search(r'(20\d\d)', filename)
            if year_pat:
                data_year = int(year_pat.group(1))

            text_body = st.text_area("输入统计数据文本:", value=string_data, height=3000)
        else:
            text_body = st.text_area("输入统计数据文本:", height=3000)

        # Get large text body on the left side and make it take up the entire height of the web page
        refresh = st.button("Refresh")
        if refresh:
            st.write('Refreshing...')

        data_list = []
        if text_body:
            data_list = parse_report(text_body)
            changed = True
            st.write(f"Take input {text_body[:100]}")

    value_list = []
    name_list = []
    if 'value_inputs' not in st.session_state:
        st.session_state['value_inputs'] = dict()

    with col2:
        col21, col22 = st.columns([1,1])
        insert_action = col21.button('INSERT THIS ROW')
        reset_values = col22.button('复原数据输入')
        if reset_values:
            st.session_state['value_inputs'].clear()

        # Create 10 text fields vertically on the right side
        city_name = st.text_input('城市名')
        data_year = st.number_input('年份', value=data_year)
        value_list.append(city_name)
        value_list.append(data_year)
        name_list.append('city_name')
        name_list.append('data_year')

        for label, val, hint in data_list:
            print(label, val, hint)
            if label not in st.session_state['value_inputs']:
                st.session_state['value_inputs'][label] = text_field(label)
            val = st.session_state['value_inputs'][label].render(val, hint)
            if val != -1:
                value_list.append(val)
                name_list.append(label)

    if insert_action and data_list and len(data_list) > 0:
        field_count = len(name_list)
        field_clauses = ['%s' for _ in range(field_count)]

        sql = 'insert into city_data(' + ','.join(name_list) + ') values(' + ','.join(field_clauses) + ')'
        upsert_start = ' ON DUPLICATE KEY UPDATE '
        upsert_middle = [f'{name} = VALUES({name})' for name in name_list[2:]]
        upsert_sql = sql + upsert_start + ','.join(upsert_middle)
        conn = get_sql_connection(pwd)
        cursor = conn.cursor()

        print(sql)
        print(tuple(value_list))

        try:
            # Insert three fields into a table named 'users' in the database
            cursor.execute(upsert_sql, tuple(value_list))

            # Commit changes to the database
            conn.commit()
            SQLSuccess()
        except mysql.connector.Error as err:
            print(f"MySQL Error: {err}")
            SQLFail(str(err))
        finally:
            if cursor:
                cursor.close()

        # Close connection with the database
        conn.close()
        changed = False

if __name__ == '__main__':
    argparser = argparse.ArgumentParser(description='parse statistic reports.')
    argparser.add_argument("--pwd", dest='pwd',
                           required=True,
                           type=str,
                           help='Password to MySQL database.')

    args = argparser.parse_args()
    print(args)
    show_page(args.pwd)
