// src/lib/utils.ts
import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs))
}

// src/lib/constants.ts
export function getImageUrl(imageName: string): string {
    return `/assets/daylilies/${imageName}`
}