'use client'

import { useEffect } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { ArrowDown, ArrowRight, ArrowUpRight, BarChart3, BellRing, Check, ChevronRight, Eye, Radar, ShieldCheck, Sparkles, Zap } from 'lucide-react'
import { motion } from 'framer-motion'
import { useAuth } from '@/contexts/AuthContext'

const capabilities = [
  {
    icon: Radar,
    title: 'Keep a close watch',
    description: 'Track competitor pages and product updates from one calm, focused workspace.',
    color: 'lavender',
  },
  {
    icon: BellRing,
    title: 'Catch meaningful changes',
    description: 'See what changed, when it happened, and where to look next.',
    color: 'mint',
  },
  {
    icon: BarChart3,
    title: 'Turn signals into context',
    description: 'Bring monitoring activity and intelligence reports together for faster research.',
    color: 'peach',
  },
]

export default function HomePage() {
  const router = useRouter()
  const { isAuthenticated, loading } = useAuth()

  useEffect(() => {
    if (!loading && isAuthenticated) router.replace('/dashboard')
  }, [isAuthenticated, loading, router])

  if (loading || isAuthenticated) {
    return <div className="min-h-screen bg-[#f8f8f5]" aria-label="Loading workspace" />
  }

  return (
    <main className="landing-shell min-h-screen overflow-hidden text-slate-900">
      <div className="landing-glow landing-glow-one" aria-hidden="true" />
      <div className="landing-glow landing-glow-two" aria-hidden="true" />

      <header className="relative z-10 mx-auto flex w-full max-w-7xl items-center justify-between px-5 py-5 sm:px-8 lg:px-10">
        <Link href="/" className="flex items-center gap-3" aria-label="Competitor Intelligence home">
          <span className="brand-mark shrink-0"><Radar className="h-5 w-5" strokeWidth={2.2} /></span>
          <span className="whitespace-nowrap text-[13px] font-bold tracking-[-0.04em] sm:text-[15px]">Competitor<span className="hidden text-slate-500 sm:inline"> Intelligence</span></span>
        </Link>
        <nav className="hidden items-center gap-8 text-sm font-medium text-slate-600 md:flex" aria-label="Main navigation">
          <a href="#how-it-works" className="transition hover:text-slate-950">How it works</a>
          <a href="#features" className="transition hover:text-slate-950">What you can track</a>
        </nav>
        <div className="flex items-center gap-2 sm:gap-3">
          <Link href="/auth/login" className="whitespace-nowrap rounded-full px-1.5 py-2 text-xs font-semibold text-slate-700 transition hover:bg-white/70 sm:px-4 sm:text-sm">Log in</Link>
          <Link href="/auth/register" className="button-ink inline-flex shrink-0 items-center gap-1.5 whitespace-nowrap rounded-full px-3 py-2.5 text-xs font-semibold text-white transition sm:gap-2 sm:px-5 sm:text-sm">
            Get started <ArrowUpRight className="h-3.5 w-3.5 sm:h-4 sm:w-4" />
          </Link>
        </div>
      </header>

      <section className="relative z-10 mx-auto grid w-full max-w-7xl items-center gap-12 px-5 pb-20 pt-12 sm:px-8 sm:pt-16 lg:grid-cols-[1.05fr_.95fr] lg:gap-10 lg:px-10 lg:pb-28 lg:pt-20">
        <motion.div initial={{ opacity: 0, y: 18 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, ease: 'easeOut' }} className="max-w-2xl">
          <div className="eyebrow-pill mb-7 inline-flex items-center gap-2 rounded-full px-3.5 py-2 text-xs font-semibold tracking-[0.01em] text-slate-700">
            <Sparkles className="h-3.5 w-3.5 text-violet-600" /> Competitive research, with a little more clarity
          </div>
          <h1 className="text-balance text-[clamp(3.1rem,7.4vw,6.2rem)] font-semibold leading-[.99] tracking-[-.075em] text-slate-950">
            See what they&apos;re doing.<br />Know what to do <span className="headline-accent">next.</span>
          </h1>
          <p className="mt-7 max-w-xl text-base leading-7 text-slate-600 sm:text-lg sm:leading-8">
            A calmer way to keep up with your market. Monitor competitor websites, spot changes, and bring your research into one clear workspace.
          </p>
          <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:items-center">
            <Link href="/auth/register" className="button-ink inline-flex items-center justify-center gap-2 rounded-full px-6 py-3.5 text-sm font-semibold text-white transition">
              Create your workspace <ArrowRight className="h-4 w-4" />
            </Link>
            <a href="#how-it-works" className="inline-flex items-center justify-center gap-2 rounded-full px-5 py-3.5 text-sm font-semibold text-slate-700 transition hover:bg-white/70">
              Take a look <ArrowDown className="h-4 w-4" />
            </a>
          </div>
          <div className="mt-8 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs font-medium text-slate-500">
            <span className="inline-flex items-center gap-1.5"><Check className="h-3.5 w-3.5 text-emerald-700" /> Your research, organized</span>
            <span className="inline-flex items-center gap-1.5"><Check className="h-3.5 w-3.5 text-emerald-700" /> Changes surfaced clearly</span>
          </div>
        </motion.div>

        <motion.div initial={{ opacity: 0, y: 24, scale: .98 }} animate={{ opacity: 1, y: 0, scale: 1 }} transition={{ duration: .7, delay: .12, ease: 'easeOut' }} className="relative mx-auto w-full max-w-[560px]">
          <div className="orbit orbit-one" aria-hidden="true" />
          <div className="orbit orbit-two" aria-hidden="true" />
          <div className="workspace-preview relative z-10 rounded-[1.75rem] p-3 sm:p-4">
            <div className="overflow-hidden rounded-[1.25rem] border border-slate-200/80 bg-white shadow-[0_22px_70px_-35px_rgba(34,38,59,.4)]">
              <div className="flex items-center justify-between border-b border-slate-100 px-5 py-4">
                <div className="flex items-center gap-2.5"><span className="brand-mark brand-mark-small"><Radar className="h-4 w-4" /></span><span className="text-xs font-bold tracking-tight text-slate-800">Workspace preview</span></div>
                <span className="rounded-full bg-slate-50 px-2.5 py-1 text-[10px] font-semibold text-slate-500">Illustrative</span>
              </div>
              <div className="grid grid-cols-2 gap-3 p-4 sm:gap-4 sm:p-5">
                <div className="preview-stat rounded-2xl bg-[#f4f2fb] p-4"><span className="text-[10px] font-semibold uppercase tracking-[.12em] text-slate-500">Competitors</span><div className="mt-3 flex min-h-10 items-center justify-between gap-2"><span className="text-base font-semibold tracking-[-.04em] text-slate-900">Stay organized</span><span className="rounded-lg bg-white/80 p-2 text-violet-700"><Eye className="h-4 w-4" /></span></div><span className="mt-1 block text-[11px] text-slate-500">Your market in one place</span></div>
                <div className="preview-stat rounded-2xl bg-[#eff6f3] p-4"><span className="text-[10px] font-semibold uppercase tracking-[.12em] text-slate-500">Changes</span><div className="mt-3 flex min-h-10 items-center justify-between gap-2"><span className="text-base font-semibold tracking-[-.04em] text-slate-900">Spot updates</span><span className="rounded-lg bg-white/80 p-2 text-emerald-700"><Zap className="h-4 w-4" /></span></div><span className="mt-1 block text-[11px] text-slate-500">Important shifts, together</span></div>
                <div className="col-span-2 rounded-2xl border border-slate-100 p-4 sm:p-5">
                  <div className="mb-5 flex items-center justify-between"><div><span className="block text-xs font-semibold text-slate-800">A clearer view of the market</span><span className="mt-1 block text-[11px] text-slate-500">Illustrative activity view</span></div><span className="rounded-full bg-slate-50 px-2.5 py-1 text-[10px] font-medium text-slate-500">Preview</span></div>
                  <div className="flex h-24 items-end gap-2 sm:h-32 sm:gap-3" aria-hidden="true">
                    {[34, 48, 39, 66, 52, 75, 61, 88, 69, 96, 79, 100].map((height, index) => <span key={index} className={`preview-bar ${index === 9 ? 'preview-bar-highlight' : ''}`} style={{ height: `${height}%` }} />)}
                  </div>
                  <div className="mt-3 flex justify-between border-t border-slate-100 pt-3 text-[9px] font-medium uppercase tracking-[.1em] text-slate-400"><span>Monitor</span><span>Understand</span><span>Respond</span></div>
                </div>
                <div className="col-span-2 flex items-center gap-3 rounded-2xl bg-[#fcf6f0] p-4"><span className="rounded-xl bg-white p-2.5 text-amber-700"><ShieldCheck className="h-4 w-4" /></span><div><span className="block text-xs font-semibold text-slate-800">Built for focused research</span><span className="mt-0.5 block text-[11px] text-slate-500">Less tab-switching. More useful context.</span></div><ChevronRight className="ml-auto h-4 w-4 text-slate-400" /></div>
              </div>
            </div>
          </div>
          <div className="floating-note floating-note-top hidden items-center gap-2 rounded-2xl px-3 py-2.5 sm:flex"><span className="rounded-lg bg-[#eee9fa] p-2 text-violet-700"><Radar className="h-4 w-4" /></span><span><b className="block text-[11px] text-slate-800">Stay in the loop</b><small className="text-[10px] text-slate-500">Your market, in focus</small></span></div>
          <div className="floating-note floating-note-bottom hidden items-center gap-2 rounded-2xl px-3 py-2.5 sm:flex"><span className="flex h-8 w-8 items-center justify-center rounded-full bg-[#e6f2eb] text-[10px] font-bold text-emerald-800">SS</span><span><b className="block text-[11px] text-slate-800">One focused workspace</b><small className="text-[10px] text-slate-500">Made for your next move</small></span></div>
        </motion.div>
      </section>

      <section id="features" className="relative z-10 border-y border-white/70 bg-white/45 px-5 py-16 sm:px-8 sm:py-20 lg:px-10">
        <div className="mx-auto max-w-7xl">
          <div className="mb-9 flex flex-col justify-between gap-4 sm:mb-11 sm:flex-row sm:items-end">
            <div><p className="section-kicker">Your research, less scattered</p><h2 className="mt-3 max-w-lg text-3xl font-semibold tracking-[-.055em] text-slate-900 sm:text-4xl">A better way to keep your eyes on the market.</h2></div>
            <p className="max-w-sm text-sm leading-6 text-slate-600">The useful details are easier to act on when they live together.</p>
          </div>
          <div className="grid gap-4 md:grid-cols-3">
            {capabilities.map(({ icon: Icon, title, description, color }, index) => <motion.article key={title} initial={{ opacity: 0, y: 14 }} whileInView={{ opacity: 1, y: 0 }} viewport={{ once: true, margin: '-40px' }} transition={{ delay: index * .08, duration: .4 }} className="capability-card rounded-3xl p-6 sm:p-7"><span className={`capability-icon capability-${color}`}><Icon className="h-5 w-5" /></span><h3 className="mt-6 text-lg font-semibold tracking-tight text-slate-900">{title}</h3><p className="mt-2 text-sm leading-6 text-slate-600">{description}</p></motion.article>)}
          </div>
        </div>
      </section>

      <section id="how-it-works" className="relative z-10 mx-auto flex max-w-7xl flex-col items-start justify-between gap-7 px-5 py-16 sm:px-8 md:flex-row md:items-center lg:px-10 lg:py-20">
        <div><p className="section-kicker">A little more signal</p><h2 className="mt-3 max-w-2xl text-3xl font-semibold leading-tight tracking-[-.055em] text-slate-900 sm:text-4xl">Make room for the work that moves you forward.</h2><p className="mt-3 max-w-xl text-sm leading-6 text-slate-600">Start with the competitors that matter. Build context over time. Decide what deserves your attention.</p></div>
        <Link href="/auth/register" className="button-ink inline-flex shrink-0 items-center gap-2 rounded-full px-6 py-3.5 text-sm font-semibold text-white transition">Explore your workspace <ArrowRight className="h-4 w-4" /></Link>
      </section>

      <footer className="relative z-10 border-t border-slate-200/70 px-5 py-6 sm:px-8 lg:px-10"><div className="mx-auto flex max-w-7xl flex-col items-center justify-between gap-3 text-xs text-slate-500 sm:flex-row"><Link href="/" className="font-semibold tracking-tight text-slate-700">Competitor Intelligence</Link><span>Competitive research, with a little more clarity.</span><Link href="/auth/login" className="font-semibold text-slate-600 transition hover:text-slate-950">Sign in <span aria-hidden="true">→</span></Link></div></footer>
    </main>
  )
}
