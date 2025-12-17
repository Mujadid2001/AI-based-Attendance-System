import { ImgHTMLAttributes, useState } from 'react'
import clsx from 'clsx'
import { IoPerson } from 'react-icons/io5'

interface AvatarProps extends Omit<ImgHTMLAttributes<HTMLImageElement>, 'size'> {
  src?: string
  alt?: string
  size?: 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'
  fallback?: React.ReactNode
}

const sizeClasses = {
  xs: 'w-6 h-6',
  sm: 'w-8 h-8',
  md: 'w-10 h-10',
  lg: 'w-12 h-12',
  xl: 'w-16 h-16',
  '2xl': 'w-24 h-24',
}

const iconSizes = {
  xs: 'w-3 h-3',
  sm: 'w-4 h-4',
  md: 'w-5 h-5',
  lg: 'w-6 h-6',
  xl: 'w-8 h-8',
  '2xl': 'w-12 h-12',
}

const Avatar = ({ 
  src, 
  alt = 'Avatar', 
  size = 'md', 
  fallback,
  className,
  ...props 
}: AvatarProps) => {
  const [imageError, setImageError] = useState(false)
  const [imageLoading, setImageLoading] = useState(true)

  const showFallback = !src || imageError || imageLoading

  return (
    <div
      className={clsx(
        'relative inline-flex items-center justify-center rounded-full overflow-hidden bg-gradient-to-br from-primary-100 to-secondary-100',
        sizeClasses[size],
        className
      )}
    >
      {src && !imageError ? (
        <img
          src={src}
          alt={alt}
          onError={() => {
            setImageError(true)
            setImageLoading(false)
          }}
          onLoad={() => setImageLoading(false)}
          className={clsx(
            'w-full h-full object-cover transition-opacity duration-200',
            imageLoading ? 'opacity-0' : 'opacity-100'
          )}
          {...props}
        />
      ) : null}
      
      {showFallback && (
        <div className="absolute inset-0 flex items-center justify-center">
          {fallback || (
            <IoPerson className={clsx('text-primary-600', iconSizes[size])} />
          )}
        </div>
      )}
    </div>
  )
}

export default Avatar
