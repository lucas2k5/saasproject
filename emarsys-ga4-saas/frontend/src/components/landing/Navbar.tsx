import { useState } from "react";
import { Link } from "react-router-dom";
import { Menu, X } from "lucide-react";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList
} from "../ui/navigation-menu";

function Navbar() {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <header className="sticky top-4 z-20 px-4 sm:px-6 lg:px-8">
      <div className="mx-auto w-full max-w-6xl">
        <div className="flex items-center justify-between rounded-full border border-white/10 bg-slate-950/80 px-6 py-4 backdrop-blur">
          <Link to="/" className="inline-flex items-center gap-2.5" aria-label="Home">
            <span className="inline-flex h-9 w-9 items-center justify-center rounded-full border-2 border-orange-500 shadow-[0_0_18px_rgba(255,122,61,0.35)]" />
            <span className="text-sm font-semibold text-white">KeepAIS</span>
          </Link>

          <div className="hidden items-center gap-6 lg:flex">
            <NavigationMenu>
              <NavigationMenuList>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    className="text-sm font-semibold text-slate-200"
                    href="#features"
                  >
                    Recursos
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    className="text-sm font-semibold text-slate-200"
                    href="#modules"
                  >
                    Módulos
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    className="text-sm font-semibold text-slate-200"
                    href="#pricing"
                  >
                    Planos
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    className="text-sm font-semibold text-slate-200"
                    href="#recommender"
                  >
                    Recomendador IA
                  </NavigationMenuLink>
                </NavigationMenuItem>
                <NavigationMenuItem>
                  <NavigationMenuLink
                    className="text-sm font-semibold text-slate-200"
                    href="#integrations"
                  >
                    Integrações
                  </NavigationMenuLink>
                </NavigationMenuItem>
              </NavigationMenuList>
            </NavigationMenu>

            <div className="flex items-center gap-3">
              <Badge variant="highlight">5 integrações nativas</Badge>
              <Button variant="ghost" asChild>
                <Link to="/login">Entrar</Link>
              </Button>
              <Button asChild>
                <Link to="/dashboard">Abrir console</Link>
              </Button>
            </div>
          </div>

          <button
            type="button"
            className="inline-flex h-10 w-10 items-center justify-center rounded-full border border-white/10 text-white lg:hidden"
            onClick={() => setIsOpen((current) => !current)}
            aria-label="Toggle menu"
          >
            {isOpen ? <X className="h-5 w-5" /> : <Menu className="h-5 w-5" />}
          </button>
        </div>

        {isOpen && (
          <div className="mt-3 flex flex-col gap-4 rounded-3xl border border-white/10 bg-slate-950/90 p-6 text-sm text-slate-200 shadow-[0_20px_40px_rgba(7,11,24,0.45)] lg:hidden">
            <div className="grid gap-2">
              <a href="#features" className="font-semibold">
                Recursos
              </a>
              <a href="#modules" className="font-semibold">
                Módulos
              </a>
              <a href="#pricing" className="font-semibold">
                Planos
              </a>
              <a href="#recommender" className="font-semibold">
                Recomendador IA
              </a>
              <a href="#integrations" className="font-semibold">
                Integrações
              </a>
            </div>
            <Badge variant="highlight">5 integrações nativas</Badge>
            <div className="flex flex-col gap-3">
              <Button variant="ghost" asChild>
                <Link to="/login">Entrar</Link>
              </Button>
              <Button asChild>
                <Link to="/dashboard">Abrir console</Link>
              </Button>
            </div>
          </div>
        )}
      </div>
    </header>
  );
}

export default Navbar;
