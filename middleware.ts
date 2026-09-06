import { createServerClient } from '@supabase/ssr'
import { NextResponse, type NextRequest } from 'next/server'

export async function middleware(request: NextRequest) {
  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseKey =
    process.env.NEXT_PUBLIC_SUPABASE_PUBLISHABLE_KEY ||
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  // Si les variables Supabase ne sont pas disponibles dans l'environnement
  // de déploiement, ne faisons pas planter tout le site au niveau middleware.
  if (!supabaseUrl || !supabaseKey) {
    return NextResponse.next()
  }

  let response = NextResponse.next({ request })

  try {
    const supabase = createServerClient(supabaseUrl, supabaseKey, {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(items) {
          items.forEach(({ name, value }) => {
            request.cookies.set(name, value)
          })
          response = NextResponse.next({ request })
          items.forEach(({ name, value, options }) => {
            response.cookies.set(name, value, options)
          })
        },
      },
    })

    const {
      data: { user },
    } = await supabase.auth.getUser()

    const pathname = request.nextUrl.pathname

    const isAuthRoute =
      pathname.startsWith('/auth') ||
      pathname.startsWith('/invite/')

    const code = request.nextUrl.searchParams.get('code')
    const type = request.nextUrl.searchParams.get('type')

    if (!user && code) {
      const resetUrl = new URL('/auth/reset-password', request.url)
      resetUrl.searchParams.set('code', code)

      if (type) {
        resetUrl.searchParams.set('type', type)
      }

      return NextResponse.redirect(resetUrl)
    }

    if (!user && !isAuthRoute) {
      return NextResponse.redirect(new URL('/auth', request.url))
    }

    if (user && pathname === '/auth') {
      return NextResponse.redirect(new URL('/', request.url))
    }
  } catch (error) {
    // Une erreur d'authentification ne doit jamais rendre le site entier
    // inaccessible. La page pourra gérer l'état de session côté client.
    console.error('Supabase middleware error:', error)
  }

  return response
}

export const config = {
  matcher: ['/((?!_next/static|_next/image|favicon.ico).*)'],
}
