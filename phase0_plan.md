# Phase 0 상세 실행 계획

## 목표
기본 개발 환경과 레이아웃, 역할 전환 구조를 잡는다.

## 추정 기간
약 1~2일 (8~16시간)

---

## Step 1: 프로젝트 초기화 (30분)

### 작업 내용
- Vite + React + TypeScript 프로젝트 생성
- Git 저장소 초기화 및 .gitignore 설정
- 기본 디렉토리 구조 설계

### 명령어
```bash
npm create vite@latest timeet -- --template react-ts
cd timeet
npm install
```

### 디렉토리 구조
```
timeet/
├── src/
│   ├── components/         # 재사용 가능한 UI 컴포넌트
│   │   ├── common/        # 공통 컴포넌트 (Button, Modal 등)
│   │   └── layout/        # 레이아웃 컴포넌트 (Header, Footer 등)
│   ├── contexts/          # React Context (상태 관리)
│   ├── pages/             # 페이지 컴포넌트
│   │   ├── Customer/      # 고객 화면
│   │   ├── Owner/         # 점주 화면
│   │   └── Admin/         # 관리자 화면
│   ├── types/             # TypeScript 타입 정의
│   ├── utils/             # 유틸리티 함수
│   ├── hooks/             # 커스텀 훅
│   ├── data/              # 목업 데이터
│   ├── App.tsx
│   └── main.tsx
├── public/
├── package.json
└── tsconfig.json
```

### 산출물
- ✅ 실행 가능한 기본 프로젝트
- ✅ 디렉토리 구조 생성

---

## Step 2: Tailwind CSS 설정 (30분)

### 작업 내용
- Tailwind CSS 및 관련 패키지 설치
- 설정 파일 생성 및 구성
- 기본 스타일 적용

### 명령어
```bash
npm install -D tailwindcss postcss autoprefixer
npx tailwindcss init -p
```

### tailwind.config.js
```js
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#f0f9ff',
          100: '#e0f2fe',
          500: '#0ea5e9',
          600: '#0284c7',
          700: '#0369a1',
        },
        confirmed: '#10b981',    // green
        pending: '#f59e0b',      // amber
        cancelled: '#ef4444',    // red
      },
    },
  },
  plugins: [],
}
```

### src/index.css
```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  body {
    @apply bg-gray-50 text-gray-900;
  }
}
```

### 산출물
- ✅ Tailwind CSS 설정 완료
- ✅ 기본 색상 팔레트 정의

---

## Step 3: 전역 상태 관리 구조 설계 (1~2시간)

### 작업 내용
- React Context API 기반 상태 관리 구조 설계
- 역할(Role) 관리 Context
- 향후 확장을 위한 기본 구조

### 파일: src/types/index.ts
```typescript
// 역할 타입
export type UserRole = 'customer' | 'owner' | 'admin';

// 예약 상태
export type ReservationStatus = 'PENDING' | 'CONFIRMED' | 'CANCELLED';

// 기본 인터페이스 (Phase 1에서 상세화)
export interface Service {
  id: string;
  name: string;
  durationMinutes: number;
  price: number;
  description?: string;
  isActive: boolean;
}

export interface Reservation {
  id: string;
  customerName: string;
  serviceId: string;
  shopId: string;
  startTime: string;  // ISO string
  endTime: string;    // ISO string
  status: ReservationStatus;
  memo?: string;
  createdAt: string;
}

export interface Shop {
  id: string;
  name: string;
  businessHours: BusinessHours;
  breakTimes: BreakTime[];
}

export interface BusinessHours {
  [key: string]: {  // 'monday', 'tuesday', etc.
    isOpen: boolean;
    start: string;  // 'HH:mm' format
    end: string;    // 'HH:mm' format
  };
}

export interface BreakTime {
  start: string;  // 'HH:mm' format
  end: string;    // 'HH:mm' format
}
```

### 파일: src/contexts/AppContext.tsx
```typescript
import React, { createContext, useContext, useState, ReactNode } from 'react';
import { UserRole } from '../types';

interface AppContextType {
  currentRole: UserRole;
  setCurrentRole: (role: UserRole) => void;
}

const AppContext = createContext<AppContextType | undefined>(undefined);

export const AppProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [currentRole, setCurrentRole] = useState<UserRole>('customer');

  return (
    <AppContext.Provider value={{ currentRole, setCurrentRole }}>
      {children}
    </AppContext.Provider>
  );
};

export const useApp = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useApp must be used within AppProvider');
  }
  return context;
};
```

### 파일: src/contexts/DataContext.tsx (기본 골격)
```typescript
import React, { createContext, useContext, useState, ReactNode } from 'react';
import { Service, Reservation, Shop } from '../types';

interface DataContextType {
  services: Service[];
  reservations: Reservation[];
  shops: Shop[];
  // CRUD 메서드는 Phase 1~2에서 추가
}

const DataContext = createContext<DataContextType | undefined>(undefined);

export const DataProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [services, setServices] = useState<Service[]>([]);
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [shops, setShops] = useState<Shop[]>([]);

  return (
    <DataContext.Provider value={{ services, reservations, shops }}>
      {children}
    </DataContext.Provider>
  );
};

export const useData = () => {
  const context = useContext(DataContext);
  if (!context) {
    throw new Error('useData must be used within DataProvider');
  }
  return context;
};
```

### 산출물
- ✅ 타입 정의 파일
- ✅ AppContext (역할 관리)
- ✅ DataContext (데이터 관리 골격)

---

## Step 4: 공통 레이아웃 구성 (2~3시간)

### 작업 내용
- Header 컴포넌트 (역할 선택 기능 포함)
- 메인 레이아웃 컴포넌트
- 기본 UI 컴포넌트 (Button, Card 등)

### 파일: src/components/layout/Header.tsx
```typescript
import React from 'react';
import { useApp } from '../../contexts/AppContext';
import { UserRole } from '../../types';

const Header: React.FC = () => {
  const { currentRole, setCurrentRole } = useApp();

  const roles: { value: UserRole; label: string }[] = [
    { value: 'customer', label: '고객' },
    { value: 'owner', label: '점주' },
    { value: 'admin', label: '관리자' },
  ];

  return (
    <header className="bg-white shadow-sm border-b border-gray-200">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between items-center h-16">
          {/* 로고 */}
          <div className="flex items-center">
            <h1 className="text-2xl font-bold text-primary-600">Timeet</h1>
          </div>

          {/* 역할 선택 */}
          <div className="flex items-center gap-4">
            <span className="text-sm text-gray-600">역할:</span>
            <select
              value={currentRole}
              onChange={(e) => setCurrentRole(e.target.value as UserRole)}
              className="px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
            >
              {roles.map((role) => (
                <option key={role.value} value={role.value}>
                  {role.label}
                </option>
              ))}
            </select>
          </div>
        </div>
      </div>
    </header>
  );
};

export default Header;
```

### 파일: src/components/layout/MainLayout.tsx
```typescript
import React, { ReactNode } from 'react';
import Header from './Header';

interface MainLayoutProps {
  children: ReactNode;
}

const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  return (
    <div className="min-h-screen bg-gray-50">
      <Header />
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {children}
      </main>
    </div>
  );
};

export default MainLayout;
```

### 파일: src/components/common/Button.tsx
```typescript
import React, { ButtonHTMLAttributes } from 'react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'danger';
  size?: 'sm' | 'md' | 'lg';
}

const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  ...props
}) => {
  const baseClasses = 'rounded-lg font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2';
  
  const variantClasses = {
    primary: 'bg-primary-600 text-white hover:bg-primary-700 focus:ring-primary-500',
    secondary: 'bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500',
    danger: 'bg-red-600 text-white hover:bg-red-700 focus:ring-red-500',
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg',
  };

  return (
    <button
      className={`${baseClasses} ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
};

export default Button;
```

### 파일: src/components/common/Card.tsx
```typescript
import React, { ReactNode } from 'react';

interface CardProps {
  children: ReactNode;
  className?: string;
}

const Card: React.FC<CardProps> = ({ children, className = '' }) => {
  return (
    <div className={`bg-white rounded-lg shadow-sm border border-gray-200 p-6 ${className}`}>
      {children}
    </div>
  );
};

export default Card;
```

### 산출물
- ✅ Header 컴포넌트 (역할 선택 UI 포함)
- ✅ MainLayout 컴포넌트
- ✅ Button, Card 등 기본 UI 컴포넌트

---

## Step 5: 페이지 컴포넌트 골격 생성 (1~2시간)

### 작업 내용
- 역할별 페이지 컴포넌트 기본 구조
- 더미 컨텐츠로 화면 전환 테스트

### 파일: src/pages/Customer/CustomerPage.tsx
```typescript
import React from 'react';
import Card from '../../components/common/Card';

const CustomerPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">고객 예약 화면</h2>
      <Card>
        <p className="text-gray-600">
          캘린더 기반 예약 시스템이 여기에 표시됩니다.
        </p>
        <p className="text-sm text-gray-500 mt-4">
          Phase 2에서 구현 예정
        </p>
      </Card>
    </div>
  );
};

export default CustomerPage;
```

### 파일: src/pages/Owner/OwnerPage.tsx
```typescript
import React from 'react';
import Card from '../../components/common/Card';

const OwnerPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">점주 대시보드</h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <Card>
          <h3 className="text-xl font-semibold mb-2">통합 예약 캘린더</h3>
          <p className="text-gray-600">Phase 3에서 구현 예정</p>
        </Card>
        <Card>
          <h3 className="text-xl font-semibold mb-2">서비스 관리</h3>
          <p className="text-gray-600">Phase 3에서 구현 예정</p>
        </Card>
      </div>
    </div>
  );
};

export default OwnerPage;
```

### 파일: src/pages/Admin/AdminPage.tsx
```typescript
import React from 'react';
import Card from '../../components/common/Card';

const AdminPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <h2 className="text-3xl font-bold text-gray-900">관리자 대시보드</h2>
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <h3 className="text-lg font-semibold">총 예약 수</h3>
          <p className="text-3xl font-bold text-primary-600 mt-2">0</p>
        </Card>
        <Card>
          <h3 className="text-lg font-semibold">확정된 예약</h3>
          <p className="text-3xl font-bold text-confirmed mt-2">0</p>
        </Card>
        <Card>
          <h3 className="text-lg font-semibold">총 매출</h3>
          <p className="text-3xl font-bold text-gray-900 mt-2">₩0</p>
        </Card>
      </div>
      <Card>
        <p className="text-gray-600">차트 및 통계는 Phase 4에서 구현 예정</p>
      </Card>
    </div>
  );
};

export default AdminPage;
```

### 산출물
- ✅ 고객/점주/관리자 페이지 골격
- ✅ 역할별로 다른 화면 표시 확인 가능

---

## Step 6: App 통합 및 테스트 (1시간)

### 작업 내용
- Context Provider 적용
- 역할에 따른 페이지 라우팅
- 전체 플로우 테스트

### 파일: src/App.tsx
```typescript
import React from 'react';
import { AppProvider, useApp } from './contexts/AppContext';
import { DataProvider } from './contexts/DataContext';
import MainLayout from './components/layout/MainLayout';
import CustomerPage from './pages/Customer/CustomerPage';
import OwnerPage from './pages/Owner/OwnerPage';
import AdminPage from './pages/Admin/AdminPage';

const AppContent: React.FC = () => {
  const { currentRole } = useApp();

  const renderPage = () => {
    switch (currentRole) {
      case 'customer':
        return <CustomerPage />;
      case 'owner':
        return <OwnerPage />;
      case 'admin':
        return <AdminPage />;
      default:
        return <CustomerPage />;
    }
  };

  return (
    <MainLayout>
      {renderPage()}
    </MainLayout>
  );
};

const App: React.FC = () => {
  return (
    <AppProvider>
      <DataProvider>
        <AppContent />
      </DataProvider>
    </AppProvider>
  );
};

export default App;
```

### 파일: src/main.tsx
```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### 테스트 체크리스트
- [ ] 프로젝트가 정상적으로 실행되는가? (`npm run dev`)
- [ ] 헤더의 역할 선택 드롭다운이 동작하는가?
- [ ] 역할 변경 시 페이지가 올바르게 전환되는가?
- [ ] Tailwind CSS 스타일이 적용되는가?
- [ ] 반응형 레이아웃이 동작하는가? (모바일/태블릿/데스크톱)

### 산출물
- ✅ 완전히 통합된 Phase 0 프로젝트
- ✅ 역할 전환이 가능한 기본 애플리케이션

---

## Step 7: 문서화 및 정리 (30분)

### 작업 내용
- README.md 작성
- package.json scripts 정리
- Git 커밋

### 파일: README.md
```markdown
# Timeet - 예약 관리 시스템

## 프로젝트 개요
매장 및 서비스 제공자를 위한 웹 기반 예약 관리 시스템

## 기술 스택
- React 18
- TypeScript
- Tailwind CSS
- Vite

## 설치 및 실행

\`\`\`bash
# 의존성 설치
npm install

# 개발 서버 실행
npm run dev

# 빌드
npm run build
\`\`\`

## 프로젝트 구조
- `/src/components` - 재사용 가능한 UI 컴포넌트
- `/src/contexts` - React Context (상태 관리)
- `/src/pages` - 페이지 컴포넌트
- `/src/types` - TypeScript 타입 정의

## 개발 현황
- [x] Phase 0: 프로젝트 세팅 완료
- [ ] Phase 1: 데이터 모델 설계
- [ ] Phase 2: 고객 화면
- [ ] Phase 3: 점주 대시보드
- [ ] Phase 4: 관리자 대시보드
- [ ] Phase 5: 반응형 & UX 마감
```

### Git 커밋
```bash
git add .
git commit -m "feat: Phase 0 완료 - 프로젝트 세팅 및 기본 구조"
```

### 산출물
- ✅ README.md
- ✅ Git 커밋 완료

---

## Phase 0 완료 체크리스트

### 필수 산출물
- [ ] React + TypeScript 프로젝트 실행 가능
- [ ] Tailwind CSS 설정 완료
- [ ] 역할 전환 기능 동작
- [ ] 고객/점주/관리자 페이지 골격 생성
- [ ] Context 기반 상태 관리 구조 완성
- [ ] 기본 UI 컴포넌트 (Button, Card) 구현
- [ ] 반응형 레이아웃 기본 동작
- [ ] README.md 작성

### 다음 단계 (Phase 1)
Phase 0 완료 후, Phase 1로 이동하여 데이터 모델과 목업 데이터를 구체화합니다.

---

## 참고 자료
- 기준 문서: `prd_2nd.md`, `dev_plan.md`
- React 공식 문서: https://react.dev
- Tailwind CSS 문서: https://tailwindcss.com
- TypeScript 문서: https://www.typescriptlang.org


