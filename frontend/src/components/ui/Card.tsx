import { motion } from 'framer-motion'
import clsx from 'clsx'
import { ReactNode } from 'react'

interface CardProps {
  children: ReactNode
  className?: string
  hoverable?: boolean
  padding?: 'none' | 'sm' | 'md' | 'lg'
  onClick?: () => void
}

const Card = ({
  children,
  className,
  hoverable = false,
  padding = 'md',
  onClick,
}: CardProps) => {
  const paddingClasses = {
    none: '',
    sm: 'p-4',
    md: 'p-6',
    lg: 'p-8',
  }

  const Component = hoverable || onClick ? motion.div : 'div'
  const motionProps = hoverable || onClick
    ? {
        whileHover: { scale: 1.02, boxShadow: '0 10px 30px rgba(0,0,0,0.15)' },
        whileTap: onClick ? { scale: 0.98 } : {},
      }
    : {}

  return (
    <Component
      className={clsx(
        'bg-white rounded-xl shadow-md transition-all',
        paddingClasses[padding],
        onClick && 'cursor-pointer',
        className
      )}
      onClick={onClick}
      {...motionProps}
    >
      {children}
    </Component>
  )
}

export default Card
