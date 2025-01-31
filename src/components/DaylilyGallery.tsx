'use client';

import React, { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTheme } from 'next-themes';
import Image from 'next/image';
import { Button } from '@/components/ui/button';
import { Daylily, FilterState, INITIAL_FILTER_STATE } from '@/types/daylily';
import { getImageUrl } from '@/lib/constants';
import FilterPanel from './FilterPanel';
import DetailView from './DetailView';
import { Card, CardContent } from './ui/card';


export default function DaylilyGallery() {
    const [mounted, setMounted] = useState(false);
    const [isFilterOpen, setIsFilterOpen] = useState(false);
    const [selectedDaylily, setSelectedDaylily] = useState<Daylily | null>(null);
    const [daylilies, setDaylilies] = useState<Daylily[]>([]);
    const [filteredDaylilies, setFilteredDaylilies] = useState<Daylily[]>([]);
    const [filters, setFilters] = useState<FilterState>(INITIAL_FILTER_STATE);
    const [page, setPage] = useState(1);
    const [hasMore, setHasMore] = useState(true);
    const { resolvedTheme, setTheme } = useTheme();

    useEffect(() => {
        setMounted(true);
        loadInitialData();
    }, []);

    const loadInitialData = async () => {
        try {
            const response = await fetch('/data/varieties.jsonl');
            const text = await response.text();
            const lines = text.split('\n').filter(line => line.trim());
            const parsedData: Daylily[] = lines.map(line => JSON.parse(line));
            setDaylilies(parsedData);
            setFilteredDaylilies(parsedData);
        } catch (error) {
            console.error('Error loading data:', error);
        }
    };

    //const filterDaylilies = useEffect(() => {
    useEffect(() => {
        let filtered = [...daylilies];

        // Name search
        if (filters.search) {
            filtered = filtered.filter(d => {
                if (filters.matchType === 'exact') {
                    return d.name.toLowerCase() === filters.search.toLowerCase();
                }
                return d.name.toLowerCase().includes(filters.search.toLowerCase());
            });
        }

        // Hybridizer
        if (filters.hybridizer) {
            filtered = filtered.filter(d => {
                if (filters.hybridizerMatchType === 'exact') {
                    return d.hybridizer.toLowerCase() === filters.hybridizer.toLowerCase();
                }
                return d.hybridizer.toLowerCase().includes(filters.hybridizer.toLowerCase());
            });
        }

        // Year range
        if (filters.yearRange.start) {
            filtered = filtered.filter(d => parseInt(d.year) >= parseInt(filters.yearRange.start));
        }
        if (filters.yearRange.end) {
            filtered = filtered.filter(d => parseInt(d.year) <= parseInt(filters.yearRange.end));
        }

        // Ploidy
        if (filters.ploidy) {
            filtered = filtered.filter(d => d.ploidy === filters.ploidy);
        }

        // Bloom size
        if (filters.bloomSize.min) {
            filtered = filtered.filter(d => {
                const size = parseFloat(d.bloom_size);
                return !isNaN(size) && size >= parseFloat(filters.bloomSize.min);
            });
        }
        if (filters.bloomSize.max) {
            filtered = filtered.filter(d => {
                const size = parseFloat(d.bloom_size);
                return !isNaN(size) && size <= parseFloat(filters.bloomSize.max);
            });
        }

        // Scape height
        if (filters.scapeHeight.min) {
            filtered = filtered.filter(d => {
                const height = parseFloat(d.scape_height);
                return !isNaN(height) && height >= parseFloat(filters.scapeHeight.min);
            });
        }
        if (filters.scapeHeight.max) {
            filtered = filtered.filter(d => {
                const height = parseFloat(d.scape_height);
                return !isNaN(height) && height <= parseFloat(filters.scapeHeight.max);
            });
        }

        // Branches
        if (filters.branches.min) {
            filtered = filtered.filter(d => {
                const branches = parseFloat(d.branches);
                return !isNaN(branches) && branches >= parseFloat(filters.branches.min);
            });
        }
        if (filters.branches.max) {
            filtered = filtered.filter(d => {
                const branches = parseFloat(d.branches);
                return !isNaN(branches) && branches <= parseFloat(filters.branches.max);
            });
        }

        // Bud count
        if (filters.budCount.min) {
            filtered = filtered.filter(d => {
                const buds = parseFloat(d.bud_count);
                return !isNaN(buds) && buds >= parseFloat(filters.budCount.min);
            });
        }
        if (filters.budCount.max) {
            filtered = filtered.filter(d => {
                const buds = parseFloat(d.bud_count);
                return !isNaN(buds) && buds <= parseFloat(filters.budCount.max);
            });
        }

        // Bloom season
        if (filters.bloomSeason.length > 0) {
            filtered = filtered.filter(d => filters.bloomSeason.includes(d.bloom_season));
        }

        // Rebloom
        if (filters.rebloom) {
            filtered = filtered.filter(d =>
                d.bloom_season?.toLowerCase().includes('rebloom') ||
                d.bloom_habit?.toLowerCase().includes('rebloom') ||
                d.notes?.toLowerCase().includes('rebloom')
            );
        }


        // Foliage type
        if (filters.foliageType) {
            filtered = filtered.filter(d => d.foliage_type === filters.foliageType);
        }

        setFilteredDaylilies(filtered);
        setPage(1);
        setHasMore(filtered.length > 20);
    }, [filters, daylilies]);

    if (!mounted) return null;

    return (
        <div className="min-h-screen bg-background">
            {/* Header */}
            <header className="fixed top-0 left-0 right-0 z-50 border-b bg-background/95 backdrop-blur">
                <div className="container mx-auto p-4">
                    <div className="flex justify-between items-center">
                        <h1 className="text-2xl font-bold">Daylily Gallery</h1>
                        <div className="flex items-center gap-2">
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => setTheme(resolvedTheme === 'dark' ? 'light' : 'dark')}
                            >
                                {resolvedTheme === 'dark' ? (
                                    <Sun className="h-5 w-5" />
                                ) : (
                                    <Moon className="h-5 w-5" />
                                )}
                            </Button>
                            <Button
                                variant="outline"
                                onClick={() => setIsFilterOpen(true)}
                            >
                                Filter & Search
                            </Button>
                        </div>
                    </div>
                </div>
            </header>

            <FilterPanel
                isOpen={isFilterOpen}
                onClose={() => setIsFilterOpen(false)}
                filters={filters}
                setFilters={setFilters}
            />

            {/* Main Content */}
            <main className="container mx-auto px-4 pt-20 pb-8">
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                    {filteredDaylilies.slice(0, page * 32).map((daylily) => (
                        <Card
                            key={daylily.name}
                            className="cursor-pointer hover:shadow-lg transition-shadow"
                            onClick={() => setSelectedDaylily(daylily)}
                        >
                            <div className="aspect-square relative">
                                <Image
                                    src={getImageUrl(daylily.image_url)}
                                    alt={daylily.name}
                                    fill
                                    sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                                    className="object-cover rounded-t-xl"
                                />
                            </div>
                            <CardContent className="p-4">
                                <h2 className="font-semibold truncate">{daylily.name}</h2>
                                <p className="text-sm text-muted-foreground">
                                    {daylily.hybridizer} ({daylily.year})
                                </p>
                            </CardContent>
                        </Card>
                    ))}
                </div>
                {hasMore && (
                    <div className="mt-8 text-center">
                        <Button onClick={() => {
                            setPage(p => p + 1);
                            setHasMore(filteredDaylilies.length > (page + 1) * 20);
                        }}>
                            Load More
                        </Button>
                    </div>
                )}
            </main>

            {selectedDaylily && (
                <DetailView
                    daylily={selectedDaylily}
                    isOpen={!!selectedDaylily}
                    onClose={() => setSelectedDaylily(null)}
                />
            )}
        </div>
    );
}