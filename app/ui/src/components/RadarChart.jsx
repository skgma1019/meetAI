import React from 'react'
import {
  Chart as ChartJS,
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend,
} from 'chart.js'
import { Radar } from 'react-chartjs-2'

// Register ChartJS modules
ChartJS.register(
  RadialLinearScale,
  PointElement,
  LineElement,
  Filler,
  Tooltip,
  Legend
)

const LABEL_MAP = {
  structure: '구조화',
  clarity: '명확성',
  brevity: '간결성',
  fluency: '유창성',
  question_fit: '질문 적합성',
  posture_stability: '자세 안정성',
  hand_control: '손동작 제어',
  head_stability: '머리 안정성',
  trust_presence: '신뢰감'
}

export default function RadarChart({ metrics, color = '#3b6ea5', label = '평가 점수' }) {
  if (!metrics || !Array.isArray(metrics) || metrics.length === 0) {
    return (
      <div style={{ height: 260, display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--muted)', fontSize: 14 }}>
        데이터가 없습니다.
      </div>
    )
  }

  const labels = metrics.map(m => LABEL_MAP[m.name] || m.note || m.name)
  const scores = metrics.map(m => m.score)

  const data = {
    labels,
    datasets: [
      {
        label,
        data: scores,
        backgroundColor: color === '#3b6ea5' ? 'rgba(59, 110, 165, 0.15)' : 'rgba(194, 104, 58, 0.15)',
        borderColor: color,
        borderWidth: 2,
        pointBackgroundColor: color === '#3b6ea5' ? '#c2683a' : '#3b6ea5',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: color,
        pointRadius: 4.5,
      },
    ],
  }

  const options = {
    scales: {
      r: {
        angleLines: {
          display: true,
          color: '#cfcec6', // var(--light-border)
        },
        grid: {
          color: '#cfcec6', // var(--light-border)
        },
        pointLabels: {
          font: {
            family: 'Gaegu',
            size: 14,
            weight: 'bold',
          },
          color: '#2b2b2b', // var(--text)
        },
        ticks: {
          display: false,
          stepSize: 20,
        },
        min: 0,
        max: 100,
      },
    },
    plugins: {
      legend: {
        display: false,
      },
      tooltip: {
        callbacks: {
          label: (context) => `${context.label}: ${context.raw}점`,
        },
        titleFont: {
          family: 'Gaegu',
        },
        bodyFont: {
          family: 'Gaegu',
        },
      },
    },
    maintainAspectRatio: false,
  }

  return (
    <div style={{ height: 250, position: 'relative' }}>
      <Radar data={data} options={options} />
    </div>
  )
}
