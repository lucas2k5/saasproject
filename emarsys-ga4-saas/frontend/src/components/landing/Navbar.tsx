import { Link } from "react-router-dom";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  NavigationMenu,
  NavigationMenuItem,
  NavigationMenuLink,
  NavigationMenuList
} from "../ui/navigation-menu";

function Navbar() {
  return (
    <header className="sticky top-6 z-20">
      <div className="mx-auto flex w-full max-w-6xl items-center justify-between rounded-full border border-white/10 bg-slate-950/80 px-6 py-4 backdrop-blur">
        <div className="flex items-center gap-3">
          <span className="inline-flex h-10 w-10 items-center justify-center rounded-full border-2 border-orange-400/90 shadow-[0_0_18px_rgba(255,122,61,0.35)]" />
          <span className="text-lg font-semibold text-white">KeepAIS</span>
        </div>

        <NavigationMenu>
          <NavigationMenuList>
            <NavigationMenuItem>
              <NavigationMenuLink className="text-sm font-semibold text-slate-200" href="#features">
                Recursos
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuLink className="text-sm font-semibold text-slate-200" href="#modules">
                Módulos
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuLink className="text-sm font-semibold text-slate-200" href="#pricing">
                Planos
              </NavigationMenuLink>
            </NavigationMenuItem>
            <NavigationMenuItem>
              <NavigationMenuLink className="text-sm font-semibold text-slate-200" href="#integrations">
                Integrações
              </NavigationMenuLink>
            </NavigationMenuItem>
          </NavigationMenuList>
        </NavigationMenu>

        <div className="flex items-center gap-3">
          <Badge variant="highlight">5 integrações nativas</Badge>
          <Button variant="ghost">Entrar</Button>
          <Button asChild>
            <Link to="/dashboard">Abrir console</Link>
          </Button>
        </div>
      </div>
    </header>
  );
}

export default Navbar;
