import Image from 'next/image';
import { cn } from '../../lib/utils';

interface ResponsiveImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  className?: string;
  priority?: boolean;
}

export function ResponsiveImage({
  src,
  alt,
  width,
  height,
  className,
  priority = false,
}: ResponsiveImageProps) {
  return (
    <div className={cn('relative w-full h-auto', className)}>
      <Image
        src={src}
        alt={alt}
        width={width}
        height={height}
        priority={priority}
        className="w-full h-auto object-contain"
        style={{
          maxWidth: '100%',
          height: 'auto'
        }}
      />
    </div>
  );
} 