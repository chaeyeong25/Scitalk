from openai import OpenAI
import streamlit as st
from io import BytesIO
from fpdf import FPDF
from pathlib import Path

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


# --- 학년 및 과목별 주요 개념 ---
curriculum_keywords = {
    "중1 과학": ["물질의 상태 변화", "기체의 성질", "소화와 순환", "지권의 변화", "빛과 파동"],
    "중2 과학": ["화학 변화", "전기 회로", "운동과 에너지", "호흡과 배설", "기후와 날씨"],
    "중3 과학": ["유전과 진화", "원자와 이온", "힘과 운동", "에너지 전환", "지구와 우주"],
    "통합과학1": ["물질의 구성", "힘과 운동", "지구 시스템", "생명 시스템"],
    "통합과학2": ["에너지 전환", "화학 반응", "생명 유지", "지구 변화"],
    "과학탐구실험1": ["실험 설계", "변인 통제", "자료 해석", "오차 분석"],
    "과학탐구실험2": ["융합 실험", "자료 처리", "과학적 탐구", "실험 보고서 작성"],
    "물리학": ["운동 법칙", "힘과 에너지", "파동과 소리", "전자기 유도"],
    "화학": ["원자 구조", "화학 결합", "산과 염기", "화학 반응식"],
    "생명과학": ["세포 구조", "광합성", "유전 원리", "생태계 평형"],
    "지구과학": ["판 구조론", "대기와 해양", "별과 은하", "지구 내부 구조"],
    "역학과 에너지": ["운동량 보존", "일과 에너지", "운동의 기술적 응용"],
    "전자기와 양자": ["전기장과 자기장", "전자기 유도", "양자역학 기초"],
    "물질과 에너지": ["물질의 상태 변화", "열역학 법칙", "에너지 보존"],
    "화학 반응의 세계": ["화학 반응 종류", "반응 속도", "평형과 역반응"],
    "세포와 물질대사": ["세포 소기관", "ATP와 에너지 대사", "효소 작용"],
    "생물의 유전": ["DNA 복제", "염색체와 유전자", "유전 질환"],
    "지구시스템과학": ["지권 순환", "물질의 순환", "지구 시스템 상호작용"],
    "행성우주과학": ["태양계", "우주 팽창", "외계 행성 탐사"],
    "과학의 역사와 문화": ["과학 혁명", "동양과 서양 과학 비교", "과학의 사회적 역할"],
    "기후변화와 환경생태": ["온실 효과", "생물 다양성", "지속 가능성"],
    "융합과학탐구": ["융합적 문제 해결", "과학기술과 사회", "과학적 의사결정"]
}

# --- 상태 저장 초기화 ---
if "student_questions" not in st.session_state:
    st.session_state.student_questions = []
if "generated_question" not in st.session_state:
    st.session_state.generated_question = ""
if "ai_answers" not in st.session_state:
    st.session_state.ai_answers = []
if "ai_feedback" not in st.session_state:
    st.session_state.ai_feedback = ""

# --- AI 질문 생성 ---
def generate_question_and_intent(topic, grade_level):
    keywords = curriculum_keywords.get(grade_level + " 과학" if grade_level.startswith("중") else grade_level, [])
    keyword_hint = f"다음 개념 중 하나 이상을 참고해서 질문을 만들어주세요: {', '.join(keywords)}." if keywords else ""

    prompt = f"""
    다음은 과학 수업 주제입니다: "{topic}"
    {keyword_hint}
    이 주제와 관련된 사고 확장 질문 1개를 생성해주세요.
    너무 노골적으로 답을 말하지 마세요.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 중고등학교 과학교사입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# --- 학생 질문에 대한 AI 응답 생성 ---
def answer_student_question(question, topic):
    if topic.lower() not in question.lower():
        return "해당 질문은 현재 학습 주제와 관련된 내용이 아닙니다. 수업 내용과 연결된 질문을 해보세요."
    prompt = f"""
    학생이 '{topic}'에 대해 다음과 같은 질문을 했습니다:
    "{question}"
    학년 수준에 맞춰 친절하고 이해하기 쉽게 과학적으로 설명해주세요.
    """
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 중고등학교 과학 선생님입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=300,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# --- 학생 답변에 대한 피드백 생성 ---
def generate_ai_feedback(student_answer, topic, level):
    keywords = curriculum_keywords.get(level + " 과학" if level.startswith("중") else level, [])
    keyword_hint = f"다음 개념 중 누락된 것이 있다면 보완해주세요: {', '.join(keywords)}." if keywords else ""

    prompt = f"""
    주제: {topic}
    학생의 답변: "{student_answer}"
    {keyword_hint}
    1. 학생의 답변을 간단히 요약하고,
    2. 그에 대한 피드백을 제공하고,
    3. 해당 학년 수준에서 적절한 과학 용어를 도입한 예시 답안을 제시해 주세요.
    질문의 답이 정해져 있지 않은 열린 질문이라면 다양한 방향의 사고를 유도해주세요.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 학생의 과학 답변을 평가하는 교사입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=600,
        temperature=0.7,
    )
    return response.choices[0].message.content.strip()

# --- AI에게 입력 주제 검증 요청 함수 ---
def verify_topic_with_ai(topic, level, subject):
    prompt = f"""
    당신은 중고등학교 과학 교육과정 전문가입니다.
    다음 정보가 주어집니다.
    학년: {level}
    과목명: {subject}
    수업 주제: "{topic}"

    이 수업 주제가 해당 학년과 과목 교육과정에 적절히 포함되어 있는지 판단해 주세요.
    적절하다면 "예", 적절하지 않다면 "아니오"로 간단히 답변하고,
    가능하다면 간단한 이유도 덧붙여 주세요.
    """

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": "당신은 교육과정 전문가입니다."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=100,
        temperature=0.0,
    )
    return response.choices[0].message.content.strip()

# --- PDF 생성 함수 ---
# PDF 생성 함수 수정
def create_pdf(level, subject, topic, question, student_answer, ai_feedback, student_questions_and_answers):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # 한글 폰트 경로 설정
    font_path = Path(__file__).parent
    pdf.add_font("Nanum", "", str(font_path / "NanumGothic.ttf"), uni=True)
    pdf.add_font("Nanum", "B", str(font_path / "NanumGothicBold.ttf"), uni=True)

    # 제목
    pdf.set_font("Nanum", "B", 16)
    pdf.cell(0, 10, "SciTalk - 과학 수업 사고 확장 결과", ln=True, align="C")
    pdf.ln(10)

    # 수업 정보
    pdf.set_font("Nanum", "", 12)
    pdf.cell(0, 8, f"학년: {level}", ln=True)
    pdf.cell(0, 8, f"과목명: {subject}", ln=True)
    pdf.cell(0, 8, f"수업 주제: {topic}", ln=True)
    pdf.ln(10)

    # 수업 질문
    pdf.set_font("Nanum", "B", 14)
    pdf.cell(0, 8, "수업 관련 질문", ln=True)
    pdf.set_font("Nanum", "", 12)
    pdf.multi_cell(0, 8, question)
    pdf.ln(10)

    # 학생 답변
    pdf.set_font("Nanum", "B", 14)
    pdf.cell(0, 8, "학생 답변", ln=True)
    pdf.set_font("Nanum", "", 12)
    pdf.multi_cell(0, 8, student_answer)
    pdf.ln(10)

    # AI Q&A
    pdf.set_font("Nanum", "B", 14)
    pdf.cell(0, 8, "학생이 했던 모든 질문과 AI 답변", ln=True)
    pdf.set_font("Nanum", "", 12)
    if student_questions_and_answers:
        for i, (q, a) in enumerate(student_questions_and_answers, start=1):
            pdf.multi_cell(0, 8, f"{i}. 질문: {q}")
            pdf.multi_cell(0, 8, f"   답변: {a}")
            pdf.ln(4)
    else:
        pdf.cell(0, 8, "질문이 없습니다.", ln=True)

    # PDF 반환
    pdf_output = BytesIO()
    pdf_bytes = pdf.output(dest="S").encode("latin-1")  # 중요: fpdf는 내부적으로 latin-1로 동작
    pdf_output.write(pdf_bytes)
    pdf_output.seek(0)
    return pdf_output


# --- Streamlit 앱 ---
st.set_page_config(page_title="SciTalk - 사고 확장 도우미", layout="wide")
st.title("🧪 SciTalk - 과학 수업 사고 확장 웹앱")

# 1. 학년 및 과목 선택
st.header("1️⃣ 해당 학년 및 과목 선택")
level = st.selectbox("학년을 선택하세요", ["중1", "중2", "중3", "고등학교"])
if level == "고등학교":
    subject = st.selectbox("과목명 (2022 개정 교육과정)", [
        "통합과학1", "통합과학2", "과학탐구실험1", "과학탐구실험2",
        "물리학", "화학", "생명과학", "지구과학",
        "역학과 에너지", "전자기와 양자", "물질과 에너지", "화학 반응의 세계",
        "세포와 물질대사", "생물의 유전", "지구시스템과학", "행성우주과학",
        "과학의 역사와 문화", "기후변화와 환경생태", "융합과학탐구"
    ])
else:
    subject = level + " 과학"

# 2. 수업 주제 입력
st.header("2️⃣ 수업 주제 입력")
topic = st.text_input("학습 주제를 입력하세요", placeholder="예: 전기 회로, 세포 호흡 등")

# 새 주제를 입력하면 검증 상태 초기화
if topic and "last_topic" in st.session_state and topic != st.session_state.last_topic:
    st.session_state.verification_done = False
    st.session_state.verified = False
    st.session_state.verification_message = ""
st.session_state.last_topic = topic

# 상태 저장: 주제 검증 결과 저장
if "verified" not in st.session_state:
    st.session_state.verified = False
if "verification_done" not in st.session_state:
    st.session_state.verification_done = False
if "verification_message" not in st.session_state:
    st.session_state.verification_message = ""

# 수업 주제가 모두 입력되었는지 확인
is_input_complete = (level != "") and (subject != "") and (topic.strip() != "")

# 검증 수행 (입력 완료 + 아직 검증 안함 상태일 때만)
if is_input_complete and not st.session_state.verification_done:
    with st.spinner("입력 주제와 교육과정 적합성 검증 중..."):
        try:
            ai_verification_result = verify_topic_with_ai(topic, level, subject)
            if "예" in ai_verification_result:
                st.session_state.verified = True
                st.session_state.verification_message = "✅ 주제가 교육과정에 적합합니다."
            else:
                st.session_state.verified = False
                st.session_state.verification_message = f"⚠️ 부적합한 주제입니다. AI 응답: {ai_verification_result}"
        except Exception as e:
            st.session_state.verified = False
            st.session_state.verification_message = f"🚫 검증 중 오류 발생: {e}"
        st.session_state.verification_done = True
elif not is_input_complete:
    st.session_state.verification_message = "✏️ 학년, 과목명, 수업 주제를 모두 입력/선택해주세요."

# 검증 결과 출력
if st.session_state.verified:
    st.success(st.session_state.verification_message)
else:
    st.warning(st.session_state.verification_message)

# 3. 질문 생성 조건 확인 및 버튼 노출 (검증 통과 시에만)
if st.session_state.get("verified", False):
    if st.button("🤖 AI 질문 생성"):
        with st.spinner("AI 질문 생성 중입니다..."):
            try:
                question_text = generate_question_and_intent(topic, level)
                st.session_state.generated_question = question_text
            except Exception as e:
                st.error(f"AI 생성 오류: {e}")

# 질문 출력
if st.session_state.generated_question:
    st.markdown("### 💡 질문")
    st.markdown(f"{st.session_state.generated_question}")

    # 학생 답변
    st.subheader("✍️ 학생 답변 작성")
    student_answer = st.text_area("답변을 입력하세요", key="answer")
    if st.button("🧠 피드백 생성"):
        if student_answer.strip():
            with st.spinner("AI 피드백 생성 중입니다..."):
                feedback = generate_ai_feedback(student_answer, topic, level)
                st.session_state.ai_feedback = feedback

    # AI 피드백 출력
    if st.session_state.ai_feedback:
        st.markdown("### 📘 AI 피드백")
        st.write(st.session_state.ai_feedback)

        st.header("📄 결과 저장")
        if st.button("💾 PDF로 저장하기"):
            pdf_file = create_pdf(
                level,
                subject,
                topic,
                st.session_state.generated_question,
                student_answer,
                st.session_state.ai_feedback,
                st.session_state.ai_answers
            )
            st.download_button(
                label="PDF 파일 다운로드",
                data=pdf_file,
                file_name=f"SciTalk_{level}_{subject}_{topic}.pdf",
                mime="application/pdf"
            )

    # 학생 질문
    st.subheader("💬 AI에게 질문하기")
    student_question = st.text_area("궁금한 점을 입력하세요", key="student_q")
    if st.button("📩 질문 보내기"):
        if student_question.strip():
            with st.spinner("AI 응답 생성 중입니다..."):
                ai_response = answer_student_question(student_question, topic)
                if "관련된 내용이 아닙니다" not in ai_response:
                    st.session_state.ai_answers.append((student_question, ai_response))
                st.markdown(f"**질문:** {student_question}")
                st.markdown(f"**답변:** {ai_response}")
        else:
            st.info("질문을 입력해주세요.")