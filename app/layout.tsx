import './globals.css'
import Nav from '@/components/Nav'
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="fr"><body><main className="shell">{children}</main><Nav/></body></html>}
