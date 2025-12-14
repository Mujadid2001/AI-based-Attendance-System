import clsx from 'clsx'

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg' | 'xl'
  className?: string
  fullScreen?: boolean
}

const LoadingSpinner = ({
  size = 'md',
  className,
  fullScreen = false,
}: LoadingSpinnerProps) => {
  const sizes = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12',
    xl: 'h-16 w-16',
  }

  const spinner = (
    <div className={clsx('animate-spin rounded-full border-b-2 border-primary-600', sizes[size], className)} />
  )

  if (fullScreen) {
    return (
      <div className="fixed inset-0 flex items-center justify-center bg-white bg-opacity-90 z-50">
        {spinner}
      </div>
    )
  }

  return spinner
}

export default LoadingSpinner
