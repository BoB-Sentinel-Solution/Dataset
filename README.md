# SeedDataset 생성   
id 1 ~ id 2000까지 총 2000개의 SeedDataset 생성

<br>   

## Dataset 제작 준비 전 라벨링   
   
<details>
<summary><b>중요정보와 라벨링 1 대 1 매칭</b></summary>
<div markdown="1">

```   
{
  "성명": "NAME",
  "전화번호": "PHONE",
  "Email": "EMAIL",
  "생년월일(출생일)": "DATE_OF_BIRTH",
  "주소(시·구·동/도로명·상세)": "ADDRESS",
  "우편번호": "POSTAL_CODE",
  "주민등록번호": "RESIDENT_ID",
  "여권번호": "PASSPORT",
  "운전면허번호": "DRIVER_LICENSE",
  "외국인 등록번호": "FOREIGNER_ID",
  "건강보험번호": "HEALTH_INSURANCE_ID",
  "사업자 등록번호": "BUSINESS_ID",
  "Tax Information Number(TIN)": "TAX_ID",
  "Social Security Number(SSN)": "SSN",
  "비상연락망(비상전화)": "EMERGENCY_CONTACT",

  "계정ID / 사용자명(로그인ID)": "USERNAME",
  "닉네임": "NICKNAME",
  "권한 / 역할(Role/Scope)": "ROLE",
  "그룹/팀 소속(접근그룹)": "GROUP",
  "비밀번호": "PASSWORD",
  "비밀번호 해시(솔트 포함)": "PASSWORD_HASH",
  "보안질문 / 답변": "SECURITY_QA",
  "다중인증 시크릿(TOTP)": "MFA_SECRET",
  "백업코드": "BACKUP_CODE",
  "최근 로그인 IP": "LAST_LOGIN_IP",
  "최근 로그인 기기": "LAST_LOGIN_DEVICE",
  "최근 로그인 브라우저": "LAST_LOGIN_BROWSER",
  "세션ID": "SESSION_ID",
  "쿠키": "COOKIE",
  "JWT": "JWT",
  "Access Token": "ACCESS_TOKEN",
  "Refresh Token": "REFRESH_TOKEN",
  "OAuth Client ID": "OAUTH_CLIENT_ID",
  "OAuth Client Secret": "OAUTH_CLIENT_SECRET",
  "API 키": "API_KEY",
  "SSH 개인키": "SSH_PRIVATE_KEY",
  "TLS 개인키": "TLS_PRIVATE_KEY",
  "PGP 개인키": "PGP_PRIVATE_KEY",
  "복구 시드/니모닉": "MNEMONIC",
  "클라우드 임시자격증명": "TEMP_CLOUD_CREDENTIAL",
  "디바이스 ID": "DEVICE_ID",
  "IMEI": "IMEI",
  "시리얼 번호": "SERIAL_NUMBER",
  "브라우저 지문": "BROWSER_FINGERPRINT",
  "SAML Assertion": "SAML_ASSERTION",
  "OIDC ID Token": "OIDC_ID_TOKEN",
  "내부 시스템 접속 URL": "INTERNAL_URL",
  "Connection String": "CONNECTION_STRING",
  "최근 로그인 일시": "LAST_LOGIN_AT",

  "계좌번호": "BANK_ACCOUNT",
  "은행명": "BANK_NAME",
  "지점명": "BANK_BRANCH",
  "예금주명": "ACCOUNT_HOLDER",
  "잔액": "BALANCE",
  "통화": "CURRENCY",
  "카드번호": "CARD_NUMBER",
  "카드 유효기간": "CARD_EXPIRY",
  "카드 소유자 이름": "CARD_HOLDER",
  "CVV/CVC": "CARD_CVV",
  "결제 비밀번호(PIN)": "PAYMENT_PIN",
  "증권계좌번호": "SECURITIES_ACCOUNT",
  "가상계좌번호": "VIRTUAL_ACCOUNT",
  "가상자산 지갑주소": "WALLET_ADDRESS",
  "IBAN": "IBAN",
  "SWIFT/BIC": "SWIFT_BIC",
  "라우팅/은행 코드": "ROUTING_NUMBER",
  "결제 승인번호(승인코드)": "PAYMENT_APPROVAL_CODE",
  "결제 게이트웨이 고객ID": "GATEWAY_CUSTOMER_ID",
  "결제 프로필 ID": "PAYMENT_PROFILE_ID",

  "거래처 회사명": "COMPANY_NAME",
  "거래처 담당자명": "BUYER_NAME",
  "고객번호": "CUSTOMER_ID",
  "멤버십ID": "MEMBERSHIP_ID",
  "주문 번호": "ORDER_ID",
  "송장번호": "INVOICE_ID",
  "환불ID": "REFUND_ID",
  "교환ID": "EXCHANGE_ID",
  "배송지 주소": "SHIPPING_ADDRESS",
  "트래킹 번호": "TRACKING_ID",
  "CRM 레코드 ID": "CRM_RECORD_ID",
  "지원 티켓번호": "TICKET_ID",
  "RMA 번호": "RMA_ID",
  "쿠폰 코드": "COUPON_CODE",
  "바우처 코드": "VOUCHER_CODE",
  "청구지 주소": "BILLING_ADDRESS",
  "Tax Invoice ID": "TAX_INVOICE_ID",
  "세금계산서 번호": "TAX_INVOICE_ID",
  "고객 메모 ID": "CUSTOMER_NOTE_ID",

  "사번(직원번호)": "EMPLOYEE_ID",
  "조직명": "ORG_NAME",
  "부서명": "DEPARTMENT_NAME",
  "직책": "JOB_TITLE",
  "고용형태": "EMPLOYMENT_TYPE",
  "입사일": "HIRE_DATE",
  "퇴사일": "LEAVE_DATE",
  "급여": "SALARY",
  "급여계좌": "BANK_ACCOUNT",
  "복지 정보": "BENEFIT_INFO",
  "보험 가입 정보": "INSURANCE_INFO",
  "인사카드": "PROFILE_INFO",
  "프로필": "PROFILE_INFO",
  "사내 전화": "OFFICE_EXT",
  "내선번호": "OFFICE_EXT",
  "출입카드": "ACCESS_CARD_ID",
  "리더기 ID": "READER_ID",
  "근무지": "WORKSITE",
  "사업장": "OFFICE_LOCATION",
  "인사평가 등급": "PERFORMANCE_GRADE",
  "인사평가 결과": "PERFORMANCE_GRADE",
  "교육 정보": "EDUCATION_CERT",
  "자격증 정보": "EDUCATION_CERT",
  "출입기록": "ACCESS_LOG",
  "온콜 배정": "DUTY_ASSIGNMENT",
  "당직 배정": "DUTY_ASSIGNMENT",
  "관리자 여부": "MANAGER_FLAG",
  "보안 교육 이수일": "TRAINING_COMPLETION_DATE",
  "보안 교육 만료일": "TRAINING_EXPIRY"
}
```
</div>
</details>   



<details>
<summary><b>라벨링 집합</b></summary>
<div markdown="1">

```
ALLOWED = {
    # 개인 식별·연락
    "NAME","PHONE","EMAIL","ADDRESS","POSTAL_CODE","DATE_OF_BIRTH","RESIDENT_ID",
    "PASSPORT","DRIVER_LICENSE","FOREIGNER_ID","HEALTH_INSURANCE_ID","BUSINESS_ID",
    "TAX_ID","SSN","EMERGENCY_CONTACT","EMERGENCY_PHONE",

    # 계정·인증
    "USERNAME","NICKNAME","ROLE","GROUP","PASSWORD","PASSWORD_HASH","SECURITY_QA",
    "MFA_SECRET","BACKUP_CODE","LAST_LOGIN_IP","LAST_LOGIN_DEVICE","LAST_LOGIN_BROWSER",
    "SESSION_ID","COOKIE","JWT","ACCESS_TOKEN","REFRESH_TOKEN","OAUTH_CLIENT_ID",
    "OAUTH_CLIENT_SECRET","API_KEY","SSH_PRIVATE_KEY","TLS_PRIVATE_KEY","PGP_PRIVATE_KEY",
    "MNEMONIC","TEMP_CLOUD_CREDENTIAL","DEVICE_ID","IMEI","SERIAL_NUMBER",
    "BROWSER_FINGERPRINT","SAML_ASSERTION","OIDC_ID_TOKEN","INTERNAL_URL",
    "CONNECTION_STRING","LAST_LOGIN_AT",

    # 금융·결제
    "BANK_ACCOUNT","BANK_NAME","BANK_BRANCH","ACCOUNT_HOLDER","BALANCE","CURRENCY",
    "CARD_NUMBER","CARD_EXPIRY","CARD_HOLDER","CARD_CVV","PAYMENT_PIN",
    "SECURITIES_ACCOUNT","VIRTUAL_ACCOUNT","WALLET_ADDRESS","IBAN","SWIFT_BIC",
    "ROUTING_NUMBER","PAYMENT_APPROVAL_CODE","GATEWAY_CUSTOMER_ID","PAYMENT_PROFILE_ID",

    # 고객·거래·지원
    "COMPANY_NAME","BUYER_NAME","CUSTOMER_ID","MEMBERSHIP_ID","ORDER_ID","INVOICE_ID",
    "REFUND_ID","EXCHANGE_ID","SHIPPING_ADDRESS","TRACKING_ID","CRM_RECORD_ID",
    "TICKET_ID","RMA_ID","COUPON_CODE","VOUCHER_CODE","BILLING_ADDRESS",
    "TAX_INVOICE_ID","CUSTOMER_NOTE_ID",

    # 조직
    "EMPLOYEE_ID","ORG_NAME","DEPARTMENT_NAME","JOB_TITLE","EMPLOYMENT_TYPE",
    "HIRE_DATE","LEAVE_DATE","SALARY","BENEFIT_INFO","INSURANCE_INFO","PROFILE_INFO",
    "OFFICE_EXT","ACCESS_CARD_ID","READER_ID","WORKSITE","OFFICE_LOCATION",
    "PERFORMANCE_GRADE","EDUCATION_CERT","ACCESS_LOG","DUTY_ASSIGNMENT","MANAGER_FLAG",
    "TRAINING_COMPLETION_DATE","TRAINING_EXPIRY"
}
```
</div>
</details>   

<br>

## SeedDataset 구성   

<details>
<summary><b>올바른 학습을 위해서 31가지 조합으로 구성</b></summary>
<div markdown="1">
  
```
크게 5가지 라벨링 카테고리가 있음.

1. 개인 식별,연락
2. 계정,인증
3. 금융, 결제
4. 고객,거래,지원
5. 조직

공평하게 모든 더하는 가짓수는

  *   5개 중 1개를 뽑는 경우: ⁵C₁ = 5
  *   5개 중 2개를 뽑는 경우: ⁵C₂ = 10
  *   5개 중 3개를 뽑는 경우: ⁵C₃ = 10
  *   5개 중 4개를 뽑는 경우: ⁵C₄ = 5
  *   5개 중 5개를 뽑는 경우: ⁵C₅ = 1
  
  이것들을 모두 더하면:
  ⁵C₁ + ⁵C₂ + ⁵C₃ + ⁵C₄ + ⁵C₅ = 5 + 10 + 10 + 5 + 1 = 31
  
  31가지의 조합으로 SeedDataset을 구성.
  
>---------------------------------------------------------------------------------<     
  
단일 카테고리(1, 2, 3, 4, 5) - 64개씩 X 5개 = 320 (完)

2개 조합 (1,2 / 1,3 / … / 4,5) - 64개씩 X 10개 = 640
= 15개 × 64개 = 960

3개 조합 (1,2,3 / … / 3,4,5) - 65개씩 X 10개 = 650

4개 조합 (1,2,3,4 / … / 2,3,4,5) - 65개씩 X 5개 = 325

5개 전체 (1,2,3,4,5) - 65개씩 X 1개 = 65
= 16개 × 65개 = 1040

960 + 1040 = 2000
```   

</div>
</details> 
