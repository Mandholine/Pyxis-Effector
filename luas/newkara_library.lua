--[[
	Copyright (c) 2026, Víctor Manuel Payares - All rights reserved.
	
	Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following
	conditions are met:
	
		* Redistributions of source code must retain the above copyright notice, this list of conditions and the following
		  disclaimer.
		* Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
		  disclaimer in the documentation and/or other materials provided with the distribution.
		* Neither the name of the EFFECTOR, your author, or the names of its contributors may be used to endorse or promote
		  products derived from this software without specific prior written permission.
	
	THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDER AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
	INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
	DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
	SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
	LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
	CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE,
	EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
--]]

--[[
	Este es un proyecto apasionado, creado por fans y para fans, diseñado para revolucionar la forma en la que creas y editas
	subtítulos de karaoke y traducciones para videos. Effector no es solo un conjunto de archivos, es una poderosa biblioteca
	de scripts .LUA que te permiten integrar de forma sencilla efectos de karaoke prediseñados de muy alta calidad, funciones
	avanzadas de edición para maximizar tu creatividad en el diseño de efectos, herramientas especializadas para el manejo de
	líneas de traducción y muchas más opciones para llevar tus proyectos gráficos al siguiente nivel. Effector cuenta con una
	amplia y robusta librería que te ofrece un sinfín de posibilidades.
	Podrás ejecutar el listado de efectos que trae por defecto, aunque su verdadero potencial reside en la capacidad de crear
	nuevas librerías personalizadas, diseñar múltiples combinaciones entre todos los efectos y funciones. En su gran mayoría,
	las funciones internas del Effector están diseñadas para emular o ejecutar casi cualquier tipo de efecto gráfico o visual
	que puedas imaginar. Además, incluí una colección de polígonos y figuras ASSdraw (shapes), para los efectos que requieren
	diseño vectorial. El uso de Effector es completamente libre y gratuito. Quiero que este proyecto te pueda servir de punto
	de partida, de plataforma de lanzamiento para que, a partir de ella, puedas crear libremente tus propios efectos, estilos
	y combinaciones. Si deseas apoyarnos, eres libre de incluir el nombre de Effector, los créditos del autor y colaboradores
	en tus proyectos, aunque no es obligatorio.
	Si tienes alguna duda, sugerencia, aporte o, por qué no, deseas formar parte del equipo de desarrollo, contacta conmigo a
	través de https://www.facebook.com/itachi.2021 Si bien animamos a la experimentación, recomendamos encarecidamente evitar
	la modificación del código interno de las funciones y librerías de Effector, a menos que poseas un conocimiento avanzado.
	La alteración sin precaución podría provocar un mal funcionamiento o la inutilización del software. ¡Deseo de corazón que
	Effector te sea de gran utilidad y que disfrutes al máximo creando con él!
--]]

	local script_name = "newkara_library.lua"
	local script_author = "vict8r"
	local script_description = "main library of functions and variables from effector"
	local script_version = "1.0.0"
	local script_update = "august 18th 2026"
	
	--CONFIGURATION VALUES
	local FONT_PRECISION = 64	--font scale for better precision output from native font system
	local SCALE_PATHS = 1000	--multiplication factor for the polygons in the clipper library
	local FP_PRECISION = 3		--floating point precision by numbers behind point (for shape points)
	local ROUND_MATRIX = 6		--number of decimal places used to round a numerical value in matrix
	local ROUND_NUM = 3			--number of decimal places used to round a numerical value
	local EPSILON = 1e-6		--if math.abs(value) < 0.000001 then the value is 0
	local RANDOM				--auxiliary variable for the ke.table.get(array, "random") function
	
	local templatesfx = {leadinfx = {}, hilightfx = {}, leadoutfx = {}, shapefx = {}, translationfx = {}}
	local ke
	
	ke = {
		
		math = {
			
			__init = function(object, default)
				--helper when a function requests a number as a parameter
				object = type(object) == "function" and object() or object or default
				object = ke.table.recurse(ke.math.__init, object) --recurse
				object = type(tonumber(object)) == "number" and tonumber(object) or object
				return object
			end, --ke.math.__init({x = "-7", y = {9, 0, {"3", "&HFF&"}}})
			
			round = function(object, decimal)
				--rounds a number to a specified number of decimal places
				object = ke.table.recurse(ke.math.round, object, decimal) --recurse
				local dec = math.floor(math.abs(ke.math.__init(decimal, 0)))
				object = tonumber(object) and math.floor(tonumber(object) * (10 ^ dec) + 0.5) / (10 ^ dec) or object
				return object
			end, --ke.math.round({1.6, 3.2, "0.9", x = "&HFF&", {false, 8.7}})
			
			rand = function(num1, num2, step, sign, range)
				--generates a random number from a specified values range
				num1, num2, step = ke.math.__init(num1), ke.math.__init(num2), ke.math.__init(step, 1)
				if type(num1) == "table" then
					local keys = ke.table.filter(num1, function(k, v) return k end, true)
					return num1[keys[ke.math.rand(#keys)]]
				end --random in table
				local function fxrand(num1, num2)
					local offset = tonumber(tostring(os.time()):sub(-3, -1))
					if not num1 and not num2 then
						return ke.math.round(math.random(), 5)
					end
					if not num2 then
						if num1 == 0 then return 0 end
						num1, num2 = 1, num1
					end
					local r1 = ke.math.round(math.min(num1, num2))
					local r2 = ke.math.round(math.max(num1, num2))
					return r1 + (math.random(r1, r2) + offset - 1) % (r2 - r1 + 1)
				end --random between two valors
				if num1 == nil then return fxrand() end
				if num2 == nil then return fxrand(num1) end
				local n1, n2 = math.min(num1, num2), math.max(num1, num2)
				step = step <= 0 and 1 or step
				if range then
					local rmin, rmax, percent = range[1], range[2], range[3] or 100
					percent = ke.math.clamp(percent, 0, 100)
					local lsize = rmin > n1 and rmin - n1 or 0
					local rsize = rmax < n2 and n2 - rmax or 0
					if ke.math.rand(0, 100) <= percent or lsize + rsize <= 0 then
						return ke.math.rand(rmin, rmax, step, sign)
					end --ke.math.rand(0, 100, 0.1, false, {20, 80, 0})
					local pick = ke.math.rand(0, lsize + rsize, step)
					return pick <= lsize and ke.math.rand(n1, rmin - 1, step, sign) or ke.math.rand(rmax + 1, n2, step, sign)
				end
				local result = n1 + fxrand(0, (n2 - n1) / step) * step
				result = result > n2 and n2 or result
				return sign and result * (-1) ^ ke.math.rand(2) or result
			end,
			
			count = function(init, step)
				--generates an independent counter to each assigned variable
				local s = ke.math.__init(step, 1)
				local i = init and ke.math.__init(init) - s or 0
				return function(mode, A, B, C)
					i = i + s
					return mode and ke.math.i(i, A, B, C)[mode] or i
				end
			end,
			
			angle = function(p1, p2, p3)
				--angle between one (and origin), two or three points (ASSDraw3 coordinates)
				local x1, y1, x2, y2, x3, y3 = table.unpack(ke.math.getnumbers(p1, p2, p3))
				if x2 == nil then
					x2, y2, x1, y1 = x1, y1, 0, 0
				end --for cartesian coordinates: ang = 360 - ang
				local a1 = math.deg(math.atan2(y1 - y2, x2 - x1))
				local a2 = (x3 and y3) and math.deg(math.atan2(y2 - y3, x3 - x2)) or nil
				a1, a2 = a1 < 0 and a1 + 360 or a1, a2 and (a2 < 0 and a2 + 360 or a2) or nil
				local ang = a2 and 180 - a1 + a2 or a1
				return ke.math.round(ang < 0 and ang + 360 or (ang > 360 and ang - 360 or ang), ROUND_NUM)
			end, --ke.math.angle({4, 5})
			
			polar = function(angle, radius, get)
				--coordinates of the point located at the assigned angle and radius, with respect to the origin (ASSDraw3 format)
				angle, radius = ke.math.__init(angle), ke.math.__init(radius)
				local px = ke.math.round( radius * math.cos(math.rad(angle)), ROUND_NUM)
				local py = ke.math.round(-radius * math.sin(math.rad(angle)), ROUND_NUM)
				return (get ~= "y" and px or py), not get and py or nil
			end, --ke.math.polar(45, 10)
			
			distance = function(p1, p2)
				--distance between two points or a point and the origin (0, 0)
				local nums, pnts = ke.math.getnumbers(p1, p2), ke.table.get({p1, p2}, "topoint")
				if pnts.n > 2 then
					return pnts:iter(function(i, p, s) return s + ke.math.distance(pnts[i], pnts[i + 1]) end, {i = {1, pnts.n - 1}})
				end --ke.math.distance(ke.shape.rectangle)
				x1, y1, x2, y2 = table.unpack(nums)
				return not x1 and 0 or ke.math.round(((x1 - (x2 or 0)) ^ 2 + (y1 - (y2 or 0)) ^ 2) ^ 0.5, ROUND_NUM)
			end, --ke.math.distance({0, 0}, {3, 4})
			
			intersect = function(s1, s2)
				--intercept point between lines defined at two segments
				local x1, y1, x2, y2, x3, y3, x4, y4 = table.unpack(ke.math.getnumbers(s1, s2))
				if (x1 == x3 and y1 == y3) or (x1 == x4 and y1 == y4) then
					return x1, y1, 0
				elseif (x2 == x3 and y2 == y3) or (x2 == x4 and y2 == y4) then
					return x2, y2, 1
				end
				local t = ((x3 - x1) * (y3 - y4) - (x3 - x4) * (y3 - y1)) / ((x2 - x1) * (y3 - y4) - (x3 - x4) * (y2 - y1))
				if (x2 - x1) * (y3 - y4) - (x3 - x4) * (y2 - y1) == 0 then
					return "parallels"
				end
				local x, y = ke.math.round(x1 + t * (x2 - x1), ROUND_NUM), ke.math.round(y1 + t * (y2 - y1), ROUND_NUM)
				return x, y, t
			end, --{ke.math.intersect("2 7 11 3 ", "4 3 6 8 ")}
			
			factk = function(n)
				--factorial of number n
				n = math.abs(math.ceil(ke.math.__init(n, 0)))
				return ke.table.iter(n, function(i, v, s) return s * v end, 1)
			end, --ke.math.factk(5)
			
			i = function(counter, A, B, C)
				--generates a numerical sequence based on predetermined algorithms
				local i = ke.math.__init(counter)
				A, B, C = ke.math.__init(A, 1), ke.math.__init(B, 1), ke.math.__init(C, 1)
				local D, E, f = A - B + 1, B - A + 1, math.floor
				local xt = function(v) return math.ceil(i / v) end
				local algorithms = {
					["+,-"] = (-1) ^ (xt(A) + 1),														-->(+,-) A-veces cada uno
					["A,B"] = A + ((B - A) / 2) * (1 + (-1) ^ xt(C)),									-->(A,B) C-veces cada uno
					["mxA"] = A * xt(B),																-->(mxA) B-veces los múltiplos de A
					["A>B"] = (A <= B) and (xt(C) - 1) % E + A or -1 * ((xt(C) - 1) % D - A),			-->(A-->B) C-veces cada uno
					["ABA"] = ((A > B)																	-->(A-->B-->A)
						and B + D - ((D - 1 - (D - 1) * xt(D - 1) + i) * (-1) ^ (xt(D - 1) + 1) + (D + 1) * (1 + (-1) ^ xt(D - 1)) / 2)
						or  A + (E - 1 - (E - 1) * xt(E - 1) + i) * (-1) ^ (xt(E - 1) + 1) + (E + 1) * (1 + (-1) ^ xt(E - 1)) / 2 - 1),
					["ABB"] = A * f(1 / i) + B * (1 - f(1 / i)),										-->(A,BB) primero A y el resto B
					["ABC"] = A * f((C * xt(C) - i + 1) / C) + B * (1 - f((C * xt(C) - i + 1) / C)),	-->(A<->BB) primer A y (C-1)veces B
					["ACB"] = A * (1 - f((C - C * xt(C) + i) / C)) + B * f((C - C * xt(C) + i) / C),	-->(AA<->B) (C-1)veces A y un B
					["N,n"] = f((i - 1) / A) + 1,														-->(N,n) los Naturales A-veces cada uno
				}
				return ke.table.filter(algorithms, function(k, v) return tostring(v) == "-0" and 0 or v end)
			end,
			
			circle = function(p1, p2, p3)
				--center and circle radius from three points
				local ps = ke.table.get({p1, p2, p3}, "topoint")
				local det = ps[1].x * (ps[2].y - ps[3].y) + ps[2].x * (ps[3].y - ps[1].y) + ps[3].x * (ps[1].y - ps[2].y)
				if math.abs(det) < EPSILON then return nil, "collineals" end
				local d1, d2, d3 = ps[1]:len() ^ 2, ps[2]:len() ^ 2, ps[3]:len() ^ 2
				local center = ((d1 * (ps[3] - ps[2]) + d2 * (ps[1] - ps[3]) + d3 * (ps[2] - ps[1])) / (2 * det)):ortho()
				local radius = center:distance(ps[1])
				return center, radius
			end, --{ke.math.circle("m 0 0 l 10 0 5 7 ")}
			
			rotate = function(p, angle, axis)
				--rotation a point p(x, y, z), about the selected axis
				p = type(p) == "function" and p() or p
				local rot_p, axis = {}, axis or "z"
				if type(p) == "string" and p:match("%-?%d[%.%d]*%s+%-?%d[%.%d]*") then
					local filter_rotation = function(x, y)
						local rot = ke.math.rotate({x, y}, angle, axis)
						return ("%s %s"):format(rot.x, rot.y)
					end
					rot_p = p:gsub("(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)", filter_rotation)
					return rot_p
				end
				angle = math.rad(ke.math.__init(angle, 0))
				local x, y, z = tonumber(p.x or p[1]) or 0, tonumber(p.y or p[2]) or 0, tonumber(p.z or p[3]) or 0
				rot_p.x = axis == "x" and x or axis == "y" and math.cos(angle) * x + math.sin(angle) * z or math.cos(angle) * x - math.sin(angle) * y
				rot_p.y = axis == "x" and math.cos(angle) * y - math.sin(angle) * z or axis == "y" and y or math.sin(angle) * x + math.cos(angle) * y
				rot_p.z = axis == "x" and math.sin(angle) * y + math.cos(angle) * z or axis == "y" and math.cos(angle) * z - math.sin(angle) * x or z
				return rot_p
			end, --ke.math.rotate(ke.shape.rectangle, 20, "z")
			
			to16 = function(num)
				--converts a number from decimal base to hexadecimal base
				num = ke.math.__init(num)
				if type(num) == "table" then
					return ke.table.recurse(ke.math.to16, num)
				end --recurse		
				return ("%X"):format(ke.math.round(num))
			end, --ke.math.to16({255, 40, x = 12})
			
			clamp = function(num, menor, mayor, cycle)
				--restricts a number between a minimum and a maximum value
				num = ke.math.__init(num, 0.5)
				if type(num) == "table" then
					return ke.table.recurse(ke.math.clamp, num, menor, mayor, cycle)
				end --ke.math.clamp({3, 7, 12}, 5, 10)
				menor, mayor = ke.math.__init(menor, 0), ke.math.__init(mayor, 1)
				local c_min, c_max, ci = math.min(menor, mayor), math.max(menor, mayor)
				if cycle then --is cyclically restricted
					num = ke.math.round(num * 10000)
					c_min = ke.math.round(c_min * 10000)
					c_max = ke.math.round(c_max * 10000)
					ci = ke.math.count(num - c_min)
					return ke.math.round(ci("ABA", c_min, c_max) / 10000, 3)
				end --math.clamp(-0.2 + 1.5m)
				return num < c_min and c_min or (num > c_max and c_max or num)
			end, --ke.math.clamp(3, 5, 10)
			
			quadratic = function(c1, c2, c3)
				--find the x values in a quadratic equation, given its three coefficients
				local d = c2 * c2 - 4 * c1 * c3
				if d > EPSILON then
					return {(-c2 - math.sqrt(d)) / (2 * c1), (-c2 + math.sqrt(d)) / (2 * c1)}
				end
				return math.abs(d) <= EPSILON and {(-c2) / (2 * c1)} or {}
			end,
			
			cubic = function(c1, c2, c3, c4)
				--find the x values in a cubic equation, given its four coefficients
				local function cbrt(x) return x >= 0 and x ^ (1 / 3) or -((-x) ^ (1 / 3)) end
				local a = 1 / c1
				local b, c, d = c2 * a, c3 * a, c4 * a
				local offset = b / 3
				local p = c - b * b / 3
				local q = (2 * b * b * b) / 27 - (b * c) / 3 + d
				local D = (q * q) / 4 + (p * p * p) / 27
				local roots = ke.table.new()
				if D > EPSILON then
					local sD = math.sqrt(D)
					local u, v = cbrt(-q / 2 + sD), cbrt(-q / 2 - sD)
					local z = u + v
					roots:insert(z - offset)
				elseif math.abs(D) <= EPSILON then
					local u = cbrt(-q / 2)
					local z1, z2 = 2 * u, -u
					roots:insert(z1 - offset)
					roots:insert(z2 - offset)
				else
					local phi = math.acos(math.max(-1, math.min(1, (-q / 2) / math.sqrt(-(p * p * p) / 27))))
					local r = 2 * math.sqrt(-p / 3)
					local z1 = r * math.cos(phi / 3)
					local z2 = r * math.cos((2 * math.pi + phi) / 3)
					local z3 = r * math.cos((4 * math.pi + phi) / 3)
					roots:insert(z1 - offset)
					roots:insert(z2 - offset)
					roots:insert(z3 - offset)
				end
				return roots("org")
			end, --ke.math.cubic(1, -3, -9, -5) --> {-1, 5}
			
			resolve = function(coefficients)
				--solves linear, quadratic, and cubic equations
				while math.abs(coefficients[1]) < EPSILON do
					table.remove(coefficients, 1)
				end
				if #coefficients > 1 then
					local c1, c2, c3, c4 = table.unpack(coefficients)
					return c4 and ke.math.cubic(c1, c2, c3, c4) or (c3 and ke.math.quadratic(c1, c2, c3) or {-c2 / c1})
				end
				return false
			end, --ke.math.resolve({1, -3, -9, -5})
			
			equation = function(coefficients, reals)
				--roots of degree n equations with ascending coefficients
				local complex = {
					["new"] = function(r, i) return {r = r or 0, i = i or 0} end,
					["add"] = function(a, b) return {r = a.r + b.r, i = a.i + b.i} end,
					["sub"] = function(a, b) return {r = a.r - b.r, i = a.i - b.i} end,
					["mul"] = function(a, b) return {r = a.r * b.r - a.i * b.i, i = a.r * b.i + a.i * b.r} end,
					["abs"] = function(a) return math.sqrt(a.r * a.r + a.i * a.i) end,
					["div"] = function(a, b)
						local d = b.r * b.r + b.i * b.i
						return {r = (a.r * b.r + a.i * b.i) / d, i = (a.i * b.r - a.r * b.i) / d}
					end
				}
				local horner = function(coeff, c)
					local n = #coeff
					local p, dp = complex.new(coeff[n], 0), complex.new()
					for i = n - 1, 1, -1 do
						dp = complex.add(complex.mul(dp, c), p)
						p = complex.add(complex.mul(p, c), complex.new(coeff[i], 0))
					end
					return p, dp
				end
				local cx = ke.table.new(coefficients)
				while math.abs(cx[cx.n]) < EPSILON do
					table.remove(cx, cx.n)
				end
				local roots, n = ke.table.new(), #cx - 1
				local radius = cx:iter(function(i, v, s) return math.max(s, 1 + math.abs(cx[i] / cx[#cx])) end, {start = 1, i = {1, n}})
				for i = 1, n do
					local angle = 2 * math.pi * (i - 1) / n
					angle = angle + 0.001 * ke.math.rand()
					roots[i] = {r = radius * math.cos(angle), i = radius * math.sin(angle)}
				end
				for iters = 1, 50 do
					local done = true
					for i = 1, n do
						local z, p, dp = roots[i], horner(cx, roots[i])
						local newton, sum = complex.div(p, dp), complex.new()
						for j = 1, n do
							sum = i ~= j and complex.add(sum, complex.div(complex.new(1, 0), complex.sub(z, roots[j]))) or sum
						end
						local corr = complex.div(newton, complex.sub(complex.new(1, 0), complex.mul(newton, sum)))
						roots[i] = complex.sub(z, corr)
						done = complex.abs(corr) <= 1e-14
					end
					if done then
						break
					end
				end --ke.math.equation({-5, -9, -3, 1})
				roots = roots:get("org", "r"):filter(function(k, c) return math.abs(c.i) < EPSILON and c.r or c end)
				roots = reals and roots:filter(function(k, c) return type(c) == "number" and c or nil end) or roots
				return roots
			end, --ke.math.equation({4, 0, -5, 8, 1})
			
			evaluate = function(coefficients, t)
				--given the coefficients, evaluate a polynomial at the value t
				local c, result = ke.table.new(coefficients)
				result = c:iter(function(i, v, s) return s * t + c[i] end, {start = c[#c], i = {#c - 1, 1, -1}})
				return result
			end,--ke.math.evaluate({5, -7}, 2) --> f(x) = 5 - 7x // f(2)
			
			equality = function(n1, n2, tolerance)
				--defines a maximum tolerance for two numbers to be considered equal
				return math.abs(n1 - n2) < 0.1 ^ (tolerance or 5)
			end,
			
			between = function(num, n1, n2)
				--returns false or true if a number is between two others
				n1, n2 = math.min(n1, n2), math.max(n1, n2)
				return num >= n1 and num <= n2
			end, --ke.math.between(3, 5, 2)
			
			getpair = function(val, defx, defy)
				--obtains a pair of numbers from a given table
				local nums = ke.math.getnumbers(val)
				local vx, vy = nums[1] or defx or 0, nums[2] or defy or nums[1] or 0
				return vx, vy
			end,
			
			normalize = function(t, accel, shape)
				--returns a normalized value between 0 and 1
				local a = accel or 1
				if type(t) == "table" then
					a = t.accel or accel or 1
					s = t.shape or shape
					t = t.t
				end
				if type(t) == "table" then
					local result, last = ke.table.new(), 0
					for _, ti in ipairs(t) do
						result:insert((ti - last) / (1 - last))
						last = ti
					end --actualiza los valores de t
					return result:filter(function(k, v) return ke.math.normalize(v, a, s) end)
				end --ke.math.normalize({t = {0.3, 0.5, 0.9}})
				t = math.abs(ke.math.__init(t))
				t = (t >= 0 and t <= 1) and t or t / (10 ^ tostring(t):match("(%d+)%.?"):len())
				t = ke.math.clamp(type(a) == "function" and a(t) or t ^ a)
				if s and s:match("m%s+%-?%d[%.%-%d mlb]*") then
					--interpolation by "y" value from shape
					local normshp = ke.recall.remember("normshp", ke.shape.new(s))
					local height, p = normshp.height, normshp:getpoint(t)
					t = height == 0 and 0 or math.abs(p.y) / height
				end --ke.math.normalize(0.25, nil, ke.shape.circle)
				return t --[0, 1]
			end, --ke.math.normalize(0.75, function(t) retrun math.sin(t * 2 * math.pi) end)
			
			ipol = function(values, t, accel, shape, size)
				--interpolation between two or more numbers
				if size then
					return ke.table.new(size, function(i) return ke.math.ipol(values, (i - 1) / (size - 1), accel, shape) end)
				end
				values = type(values) == "number" and {0, values} or values
				if ke.table.type(values) == "table" then
					values = ke.table.get(values, "zip")
					return ke.table.filter(values, function(k, v) return ke.math.ipol(v, t, accel, shape, size) end)
				end --ke.math.ipol({{10, 50}, {20, 150}}, 0.5)
				t = ke.math.normalize(t, accel, shape)
				if t == 0 then
					return values[1]
				end --ke.math.ipol({0, 30, 20}, 0.25, 0.8, ke.shape.circle)
				local n = #values
				local seg = math.ceil(t * (n - 1))
				local ini, fin = values[seg], values[seg + 1]
				local u = t * (n - 1) - (seg - 1)
				return ke.math.round(ini + u * (fin - ini), ROUND_NUM)
			end, --ke.math.ipol({0, 30, 20}, 0.7)
			
			format = function(str, ...)
				--assigns values to a format string
				str = type(str) == "function" and str() or str
				local values = type(... or true) == "table" and ... or {...}
				values = #values == 0 and {1} or values
				if type(str) == "table" then
					return ke.table.recurse(ke.math.format, str, ...)
				end --recurse
				local icount = ke.string.count(str, "%%[aAcdeEfgGioqsuxX]^*") -- string.format modes
				local str = str:format(unpack(ke.table.get(values, "newlen", icount)))
				return ke.string.toval(str)
			end, --ke.math.format({"5 + 7", "%s"}, 8)
			
			getnumbers = function(...)
				--returns a single table of numbers, obtained from the entered values
				local array, getnums = {...}, ke.table.new()
				array = (#array == 1 and type(array[1]) == "table") and array[1] or array
				array = ke.table.get(array, "tonumber")
				ke.table.iter(array, function(k, v) getnums:insert(tonumber(v)) end)
				return getnums
			end, --ke.math.getnumbers({{x = 1, y = 2}, "7 8 ", 3, 4, x = 10, y = 11})
			
			gauss = function(matrix)
				--find the solutions to an (n x n) system of equations
				local n = #matrix
				local A = ke.table.copy(matrix)
				for k = 1, n do
					local max_val = math.abs(A[k][k])
					local pivot_row = k
					for i = k + 1, n do
						if math.abs(A[i][k]) > max_val then
							max_val = math.abs(A[i][k])
							pivot_row = i
						end
					end
					if max_val < EPSILON then
						return nil, "singular system"
					end
					if pivot_row ~= k then
						local temp_row = A[k]
						A[k] = A[pivot_row]
						A[pivot_row] = temp_row
					end
					local pivot = A[k][k]
					for j = k, n + 1 do
						A[k][j] = A[k][j] / pivot
					end
					for i = k + 1, n do
						local factor = A[i][k]
						for j = k, n + 1 do
							A[i][j] = A[i][j] - factor * A[k][j]
						end
					end
				end
				local solutions = {}
				for i = n, 1, -1 do
					local sum = 0
					for j = i + 1, n do
						sum = sum + A[i][j] * solutions[j]
					end
					solutions[i] = A[i][n + 1] - sum
				end
				return ke.math.round(solutions, ROUND_MATRIX)
			end, --ke.math.gauss({{5, -3, -1}, {2, 1, 4}})
			
			matrix = { --subclass
				
				__name = "matrix",
				__metatable = "matrix",
				__index = function(self, key)
					local __cache = rawget(self, key)
					if __cache ~= nil then
						return __cache
					end
					if key == "n" then
						return #self
					elseif key == "det" then
						return self:determinant()
					end
					return ke.math.matrix[key]
				end,
				
				__mul = function(self, other)
					local result = {}
					local n = self.n
					if type(self[1]) == "number" and getmetatable(other) == "matrix" then
						n = other.n --row matrix * matrix
						for j = 1, n do
							local sum = 0
							for k = 1, n do
								sum = sum + (self[k] or 0) * other[k][j]
							end
							result[j] = sum
						end
						return ke.math.matrix.new(result, true)
					end
					if type(other) == "number" then --matrix * scalar
						for i = 1, n do
							result[i] = {}
							for j = 1, n do
								result[i][j] = self[i][j] * other
							end
						end
						return ke.math.matrix.new(result)
					end
					if ke.table.type(other) == "point" then --matrix * point
						local vals, result = ke.math.getnumbers(other), {}
						for i = 1, n do
							result[i] = 0
							for j = 1, n do
								result[i] = result[i] + self[i][j] * (vals[j] or 0)
							end
						end --ke.math.matrix.__mul(ke.math.matrix.new({1,0,0,0,1,0,0,0,1}), ke.shape.point.new("l 10 20 "))
						local newp = ke.shape.point.new(result[1], result[2], other.t)
						newp.z, newp.w = result[3], result[4]
						return newp --point
					end
					for i = 1, n do --matrix * matrix
						result[i] = {}
						for j = 1, n do
							local sum = 0
							for k = 1, n do
								sum = sum + self[i][k] * other[k][j]
							end
							result[i][j] = sum
						end
					end
					return ke.math.matrix.new(result)
				end, --ke.math.matrix.new({2, 3, 1, 4, 1, -3, 2, 4, 1}) * 2
				
				__add = function(self, other)
					local result = {}
					local isrow = type(self[1]) == "number"
					for i = 1, self.n do
						result[i] = {}
						for j = 1, self.n do
							result[i][j] = self[i][j] + (type(other) == "number" and other or other[i][j])
						end
					end
					return ke.math.matrix.new(result, isrow)
				end,
				
				__sub = function(self, other)
					local result = {}
					local isrow = type(self[1]) == "number"
					for i = 1, self.n do
						result[i] = {}
						for j = 1, self.n do
							result[i][j] = self[i][j] - (type(other) == "number" and other or other[i][j])
						end
					end
					return ke.math.matrix.new(result, isrow)
				end,
				
				__unm = function(self)
					local result = {}
					local isrow = type(self[1]) == "number"
					for i = 1, self.n do
						result[i] = {}
						for j = 1, self.n do
							result[i][j] = -self[i][j]
						end
					end
					return ke.math.matrix.new(result)
				end,
				
				__eq = function(self, other)
					if self.n ~= other.n then
						return false
					end
					for i = 1, self.n do
						for j = 1, self.n do
							if not math.abs(self[i][j] - other[i][j]) < EPSILON then
								return false
							end
						end
					end
					return true
				end,
				
				__tostring = function(self)
					local s = "matrix" .. self.n .. "x" .. self.n .. "(\n"
					for i = 1, self.n do
						s = s .. "\t{"
						for j = 1, self.n do
							s = s .. string.format("%s", self[i][j])
							if j < self.n then s = s .. ", " end
						end
						s = s .. "}"
						if i < self.n then s = s .. ",\n" end
					end
					s = s .. "\n)"
					return s
				end,
				
				__type = function(self)
					return "matrix"
				end,
				
				new = function(data, isrow)
					local array = ke.table.type(data) == "matrix" and ke.math.matrix.toarray(data) or ke.math.getnumbers(data)
					local len = array.n
					if isrow then
						array = ke.math.round(array, ROUND_MATRIX)
						setmetatable(array, ke.math.matrix)
						return array
					end
					local n = math.sqrt(math.ceil(math.sqrt(len)) ^ 2)
					for i = 1, n * n do
						array[i] = ke.math.round(array[i] or 0, ROUND_MATRIX)
					end
					local m = array("inpack", n)
					setmetatable(m, ke.math.matrix)
					return m
				end, --ke.math.matrix.new({1,2,3,4})
				
				toarray = function(self)
					local result = ke.table.new()
					local n = self.n
					for i = 1, n do
						for j = 1, n do
							result:insert(self[i][j])
						end
					end
					return result
				end, --ke.math.matrix.toarray(ke.math.matrix.new({1,2,3,4}))
				
				identity = function(n)
					n = math.ceil(n)
					local data = {}
					for i = 1, n do
						data[i] = {}
						for j = 1, n do
							data[i][j] = (i == j) and 1 or 0
						end
					end
					return ke.math.matrix.new(data)
				end,  --ke.math.matrix.identity(4)
				
				determinant = function(self)
					local n = self.n
					if n == 1 then
						return self[1][1]
					end
					local det, sign = 0, 1
					for j = 1, n do
						local element = self[1][j]
						local sub_m_data = {}
						local sub_row_idx = 1
						for row = 2, n do
							sub_m_data[sub_row_idx] = {}
							local sub_col_idx = 1
							for col = 1, n do
								if col ~= j then
									sub_m_data[sub_row_idx][sub_col_idx] = self[row][col]
									sub_col_idx = sub_col_idx + 1
								end
							end
							sub_row_idx = sub_row_idx + 1
						end
						local sub_matrix = ke.math.matrix.new(sub_m_data)
						det = det + sign * element * ke.math.matrix.determinant(sub_matrix)
						sign = -sign
					end
					return det
				end, --ke.math.matrix.new({2, 3, 4, 1}).det
				
				inverse = function(self)
					local det = self.det
					if math.abs(det) < EPSILON then
						return nil
					end
					local n = self.n
					local inv_m_data = {}
					local cofactor_matrix_data = {}
					for i = 1, n do
						cofactor_matrix_data[i] = {}
						for j = 1, n do
							local sub_m_data = {}
							local sub_row_idx = 1
							for row = 1, n do
								if row ~= i then
									sub_m_data[sub_row_idx] = {}
									local sub_col_idx = 1
									for col = 1, n do
										if col ~= j then
											sub_m_data[sub_row_idx][sub_col_idx] = self[row][col]
											sub_col_idx = sub_col_idx + 1
										end
									end
									sub_row_idx = sub_row_idx + 1
								end
							end
							local cofactor = 1
							if n > 1 then
								local sub_matrix = ke.math.matrix.new(sub_m_data)
								cofactor = ke.math.matrix.determinant(sub_matrix)
							end
							cofactor = (i + j) % 2 == 1 and -cofactor or cofactor
							cofactor_matrix_data[i][j] = cofactor
						end
					end
					for i = 1, n do
						inv_m_data[i] = {}
						for j = 1, n do
							inv_m_data[i][j] = cofactor_matrix_data[j][i] / det
						end
					end
					local inv_matrix = ke.math.matrix.new(inv_m_data)
					return inv_matrix --ke.math.matrix.new({2, 3, 1, 4, 1, -3, 2, 4, 1}):inverse()
				end, --ke.math.matrix.new({2, 3, 4, 1}):inverse()
				
				rotate = function(self, angles)
					local axis = {x = angles.x or 0, y = angles.y or 0, z = angles.z or 0}
					local sx, sy, sz = math.sin(math.rad(axis.x)), math.sin(math.rad(axis.y)), math.sin(math.rad(axis.z))
					local cx, cy, cz = math.cos(math.rad(axis.x)), math.cos(math.rad(axis.y)), math.cos(math.rad(axis.z))
					local matrix_rot = {
						[1] = cy * cz,	[2] = -cx * sz + sx * sy * cz,	[3] = sx * sz + cx * sy * cz,
						[4] = cy * sz,	[5] = cx * cz + sx * sy * sz,	[6] = -sx * cz + cx * sy * sz,
						[7] = -sy,		[8] = sx * cy,					[9] = cx * cy
					}
					return self * ke.math.matrix.new(matrix_rot)
				end, --ke.math.matrix.new({4, 0}, true):rotate()
				
			},
			
		},
		
		table = {
			__name = "ketable",
			
			["__index"] = function(self, key)
				local __cache = rawget(self, key)
				if __cache ~= nil then
					return __cache
				end
				return key == "n" and #self or ke.table[key]
			end,
			
			["new"] = function(array, support)
				local newself, e = {}
				if type(array) == "table" then
					newself = ke.table.copy(array)
					if type(support) == "function" then
						for k, v in pairs(newself) do
							newself[k] = support(k, v, newself)
						end
					elseif support then
						newself = {}
						local key, val
						for i, v in ipairs(array) do
							key = type(v) == "string" and v or nil
							if key then
								val = type(support) == "table" and support[i] or nil
								val = type(support) ~= "table" and support or val
								newself[key] = val
							end
						end --ke.table.new({"w", "h"}, true)
					else
						for k, v in pairs(newself) do
							v = type(v) == "table" and ke.table.new(v) or v
							newself[k] = v
						end
					end
				elseif type(array) == "function" then
					--iterable function
					for A, B, C, D, E, F, G, H, M, N in array do
						local values = {A, B, C, D, E, F, G, H, M, N}
						if type(support) == "function" then
							for i, v in ipairs(values) do
								values[i] = support(i, v)
							end
						end
						local settab = type(support) == "number" and values[support] or (#values > 1 and values or values[1])
						table.insert(newself, settab) --ke.table.new(unicode.chars("demo"), 1)
					end --ke.table.new(shp:gmatch("(%d+) (%d+)"))
				elseif type(array) == "number" then
					local size = math.ceil(math.abs(array))
					for i = 1, size do
						e = not support and i or (type(support) ~= "function" and support or support(i))
						newself[#newself + 1] = type(e) == "table" and ke.table.copy(e) or e or nil
					end
				else
					newself = {array}
				end
				setmetatable(newself, ke.table)
				return newself
			end,
			
			["__call"] = function(self, mode, support)
				return mode and self:get(mode, support) or self:view()
			end,
			
			["__copy"] = function(array)
				local lookup = {}
				local function table_copy(array)
					if type(array) ~= "table" then
						return array
					elseif lookup[array] then
						return lookup[array]
					end
					local newself = {}
					lookup[array] = newself
					for k, v in pairs(array) do
						newself[table_copy(k)] = table_copy(v)
					end
					return setmetatable(newself, getmetatable(array))
				end
				return table_copy(array)
			end,
			
			["__sub"] = function(self, remove)
				--remove from the array the elements with the indicated indices
				return self:get("delete", remove)
			end,
			
			["__add"] = function(self, insert)
				--inserts at the end of the array, the element or the "insert" array
				return self:get("insert", insert)
			end,
			
			["__eq"] = function(self, other)
				--returns "false" or "true" when comparing two arrays
				if type(self) ~= type(other) then
					return false
				elseif type(self) ~= "table" and type(other) ~= "table" then
					return self == other
				end
				for k, v in pairs(self) do
					if (not other[k] or not ke.table.__eq(v, other[k]))
						or (other[k] and getmetatable(v) and getmetatable(v).__eq and v ~= other[k]) then
						return false
					end
				end
				return true
			end,
			
			view = function(array, isfunct)
				--returns the complete contents of an array in string mode
				local array = type(array) == "function" and array() or array
				local cart, autoref
				local isemptytable = function(array)
					return next(array) == nil
				end
				local function basicserialize(o)
					local so = tostring(o)
					if type(o) == "function" then
						if isfunct then
							return isfunct
						else
							local info = debug.getinfo(o, "S")
							if info.what == "C" then
								return ("%q"):format(so .. ", C function")
							end
							return ("%q, defined in (lines: %s - %s), ubication %s"):format(
								so, info.linedefined, info.lastlinedefined, info.source
							)
						end
					elseif type(o) == "number" or type(o) == "boolean" then
						return so
					end
					return ("%q"):format(so)
				end
				local function addtocart(value, name, indent, saved, field)
					indent, saved, field = indent or "", saved or {}, field or name
					cart = cart .. indent .. field
					if type(value) ~= "table" then
						cart = cart .. " = " .. basicserialize(value) .. ",\n"
					else
						if saved[value] then
							cart = cart .. " = {}, -- " .. saved[value] .. " (self reference)\n"
							autoref = autoref ..  name .. " = " .. saved[value] .. ",\n"
						else
							saved[value] = name
							if isemptytable(value) then
								cart = cart .. " = {},\n"
							else
								cart = cart .. " = {\n"
								for k, v in pairs(value) do
									k = basicserialize(k)
									local fname = ("%s[%s]"):format(name, k)
									field = ("[%s]"):format(k)
									addtocart(v, fname, indent .. "	", saved, field)
								end
								cart = ("%s%s},\n"):format(cart, indent)
							end
						end
					end
				end
				local name = type(array) == "table" and array.__name or "fxtable"
				name = (type(array) == "table" and array.__type) and (type(array.__type) == "function" and array:__type() or "fxtable") or name
				array = (type(array) == "table" and array.__view) and array:__view() or array
				if type(array) ~= "table" then
					return ("%s = %s"):format(name, basicserialize(array))
				end
				cart, autoref = "", ""
				addtocart(array, name, indent)
				local array2string = cart:sub(1, -3) .. "\n" .. autoref
                array2string = array2string:gsub(",\n([	]*)}", "\n%1}")
                return array2string
			end,
			
			copy = function(self)
				--makes a deep copy of a table
				return ke.table.__copy(self)
			end,
			
			clear = function(self)
				--deletes the contents of an object or a table
				local array = ke.table.copy(self)
				for key in pairs(array) do
					array[key] = nil
				end
				return array
			end,
			
			recurse = function(funct, array, ...)
				if type(array) ~= "table" then return array end
				for key, val in pairs(array) do
					if type(val) == "table" then
						ke.table.recurse(funct, val, ...)
					else
						array[key] = val
						local TRUE, valor = pcall(funct, val, ...)
						if TRUE then
							array[key] = valor
						end
					end
				end
				return array
			end, --ke.table.recurse(function(v, a) return v ^ (2 + a) end, {3, 6, "S", 5, {false, 4}}, 1)
			
			setvalues = function()
				--provides a layered environment over _G, allowing dynamic globals injection, clearing, and restoration
				local env, installed = {}, false
				local metax = getmetatable(_G) or {}
				local function install_layer()
					if installed then return end
					setmetatable(_G, {
						__index = function(_, key)
							if env[key] ~= nil then
								return env[key]
							end
							return rawget(_G, key) or (metax and metax.__index and metax.__index(key))
						end,
						__newindex = function(_, key, value)
							env[key] = value
						end
					})
					installed = true
				end
				return {
					["set"] =  function(array)
						install_layer()
						for k, v in pairs(array) do
							env[k] = v
						end
					end,
					["reset"] = function()
						setmetatable(_G, metax)
						installed = false
					end,
					["clear"] = function()
						for k in pairs(env) do
							env[k] = nil
						end
					end
				}
			end,
			
			insert = function(self, e, index, _unpack_)
				--"improved" version of the table.insert function
				local newindex = index or #self + 1
				if type(newindex) == "function" then
					local idxs = {}
					for k, v in ipairs(self) do
						if newindex(k, v, self) then
							table.insert(idxs, k)
						end
					end
					for i = #idxs, 1, -1 do
						table.insert(self, idxs[i] + 1, e)
					end
					if #idxs == 0 then
						table.insert(self, e)
					end --tbl = {1, 2, -6, -7, 8}
					--ke.table.insert(tbl, 0, function(k, v, self) return k < #self and v * self[k + 1] < 0 end)
				else
					newindex = (type(newindex) == "number" and newindex < 0) and newindex % #self + 2 or newindex
					if type(newindex) ~= "number" or (type(newindex) == "number" and newindex > #self + 1) then
						newindex = #self + 1
					end
					local idx = ke.math.count()
					if type(e) == "table" and _unpack_ then
						for k, v in pairs(e) do
							local nk = type(k) == "number" and newindex + idx() - 1 or k
							if type(nk) == "number" then
								table.insert(self, nk, v)
							else
								self[nk] = v
							end
						end
					else
						if type(newindex) == "number" then
							table.insert(self, newindex, e)
						else
							self[newindex] = e
						end
					end
				end
			end,
			
			iter = function(self, funct, configs)
				--apply the function to the elements of a table
				self = type(self) == "number" and ke.table.new(self, function(i) return i end) or self
				local start = type(configs) == "table" and configs.start or nil
				local index = type(configs) == "table" and configs.i or nil
				start = type(configs) == "number" and configs or start or 0
				local result = start --or ke.table.clear(self or {})
				local env = ke.table.setvalues()
				env.set({self = self})
				if index then
					local i1, i2, i3 = index[1] or 1, index[2] or self.n or #self or 1, index[3] or 1
					for i = i1, i2, i3 do
						local v = self and self[i] or true
						local TRUE, valor = pcall(funct, i, v, result)
						if TRUE and type(result) == "table" then
							table.insert(result, valor)
						elseif TRUE then
							result = valor
						end
					end --ke.table.iter({1, 2, 3, "d", x = 4, 5}, function(i, v, s) return s + v end)
				else
					for k, v in pairs(self) do
						local TRUE, valor = pcall(funct, k, v, result)
						if TRUE and type(result) == "table" then
							result[k] = valor
						elseif TRUE then
							result = valor
						end
					end --ke.table.iter({1, 2, 3, "d", x = 4, 5}, function(k, v) return v ^ 3 end, {start = {}})
				end
				env.reset()
				return result
			end, --5! = ke.table.iter(5, function(k, v, s) return s * v end, 1)
			
			type = function(self)
				--indicates the elements type in an array
				local self, tpx = type(self) ~= "table" and {self} or self, {}
				if pcall(function() return self:__type() end) then
					return self:__type()
				end
				for _, v in pairs(self) do
					if pcall(function() return v:__type() end) then
						tpx[#tpx + 1] = v:__type()
					elseif type(v) == "string" then
						tpx[#tpx + 1] = v:match("m%s+%-?%d[%.%-%d mlb]*") and "shape"
						or (v:match("%-?%d[%.%d]*,[]*%-?%d[%.%d]*,[]*%-?%d[%.%d]*,[]*%-?%d[%.%d]*") and "clip")
						or (v:match("%x%x%x%x%x%x") and "color")
						or (v:match("%x%x") and "alpha")
						or (v:match("\\\\") and "tag") or "string"
					else
						tpx[#tpx + 1] = type(v)
					end
					if #tpx > 1 then
						tpx[#tpx] = (tpx[#tpx] == "number" and tpx[#tpx - 1] == "alpha") and "alpha" or tpx[#tpx]
						tpx[#tpx - 1] = (tpx[#tpx] == "alpha" and tpx[#tpx - 1] == "number") and "alpha" or tpx[#tpx - 1]
						if tpx[#tpx] ~= tpx[#tpx - 1] then
							return "mixed"
						end
					end --ke.table.type({25, "&HFF&", 80})
				end
				return #tpx > 0 and tpx[1] or "empty"
			end,
			
			compare = function(self, other)
				--returns "false" or "true" when comparing two arrays
				if type(self) ~= type(other) then
					return false
				elseif type(self) ~= "table" and type(other) ~= "table" then
					return self == other
				end
				local mt = getmetatable(self)
				if mt and mt.__eq then
					return self == other
				end
				for k, v in pairs(self) do
					if not other[k] or not ke.table.compare(v, other[k]) then
						return false
					end
				end
				return true
			end,
			
			concat = function(self, ...)
				--special concatenations between arrays
				local self = type(self) == "function" and self() or self
				local concats, Helpers = {...}
				if #concats == 0 then
					local aux = self[1]
					table.remove(self, 1)
					concats, self = ke.table.copy(self), ke.table.copy(aux)
				end
				Helpers = {
					[1] = function()
						local tbls = ke.table.get(concats, "outpack")
						local con1 = ke.table.new(#self * #tbls,
							function(i)
								return self[#self - #self * math.ceil(i / #self) + i] .. tbls[math.ceil(i / #self)]
							end
						)
						return con1
					end, --ke.table.concat({"\\1a"}, {"&HFF&", "&HAB&", "&H00&"})(1) = {"\\1a&HFF&", "\\1a&HAB&", "\\1a&H00&"}
					[2] = function()
						local tbls, con2 = ke.table.get(concats, "outpack"), ke.table.new(#self, "")
						for i = 1, #self do
							for k = 1, #tbls do
								con2[i] = con2[i] .. self[i] .. tbls[k]
							end
						end
						return con2
					end, --ke.table.concat({"\\foo", "\\bar"}, {0, 255})(2) = {"\\foo0\\foo255", "\\bar0\\bar255"}
					[3] = function()
						local tbls, con3 = ke.table.copy(concats), ke.table.copy(self)
						for i = 1, #tbls do
							tbls[i] = type(tbls[i]) ~= "table" and {tbls[i]} or tbls[i]
						end
						for i = 1, #self do
							for k = 1, #tbls do
								con3[i] = con3[i] .. tbls[k][(i - 1) % #tbls[k] + 1]
							end
						end
						return con3
					end, --ke.table.concat({"A", "B", "C"}, "1", {"x", "y"})(3) = {"A1x", "B1y", "C1x"}
					[4] = function()
						local tbls, con4 = ke.table.copy(concats), ke.table.copy(self)
						for i = 1, #tbls do
							tbls[i] = type(tbls[i]) ~= "table" and {tbls[i]} or tbls[i]
						end
						for i = 1, #self do
							for k = 1, #tbls do
								con4[i] = con4[i] .. (tbls[k][i] or "")
							end
						end
						return con4
					end, --ke.table.concat({"a", "b", "c", "d"}, {1, 2, 3})(4) = {"a1", "b2", "c3", "d"}
					[5] = function()
						local tbls = ke.table.copy(concats)
						for i = 1, #tbls do
							tbls[i] = type(tbls[i]) ~= "table" and {tbls[i]} or tbls[i]
						end
						local con5 = ke.table.new(#self * #tbls[1],
							function(i)
								return self[math.ceil(i / #tbls[1])] .. tbls[1][#tbls[1] - #tbls[1] * math.ceil(i / #tbls[1]) + i]
							end
						)
						for k = 2, #tbls do
							con5 = ke.table.new(#con5 * #tbls[k],
								function(i)
									return con5[math.ceil(i / #tbls[k])] .. tbls[k][#tbls[k] - #tbls[k] * math.ceil(i / #tbls[k]) + i]
								end
							)
						end
						return con5
					end, --ke.table.concat({"a", "b", "c"}, {1, 2}, "x")(5) = {"a1x", "a2x", "b1x", "b2x", "c1x", "c2x"}
					[6] = function()
						local tbls = ke.table.copy(concats)
						table.insert(tbls, 1, self)
						local size_tbl = ke.table.new(#tbls, function(i) return #tbls[i] end)
						local min_size = ke.table.get(size_tbl, "min")
						local con6 = ke.table.new(min_size, {})
						for i = 1, min_size do
							for k = 1, #tbls do
								con6[i][k] = tbls[k][i]
							end
							con6[i] = table.concat(con6[i])
						end
						return con6
					end, --ke.table.concat({{1, 2, 3, 4}, {"A", "B", "C", "D"}, {7, 8, 9, 0, -1}})(6) = {"1A7", "2B8", "3C9", "4D0"}
				}
				return function(n) return Helpers[n]() end
			end,
			
			hidden = function(array)
				--create an array with hidden attributes
				local hidden_data = {}
				return setmetatable(array, {
					["__index"] = function(array, key)
						return hidden_data[key]
					end,
					["__newindex"] = function(array, key, value)
						hidden_data[key] = value
					end,
					["__pairs"] = function()
						return next, array, nil
					end --solo lo visible
				})
			end,
			
			inside = function(self, e, capture)
				--returns "false" or "true" if an element, capture or element type, is inside an array
				if type(e) == "table" then
					for _, v in pairs(self) do
						if ke.table.compare(v, e) then
							return true
						end
					end --if "e"(array) is inside an array
				elseif type(e) == "string" then
					for _, v in pairs(self) do
						if ke.table.type(v) == e
							or ((capture and type(v) == "string") and v:match(capture) == e:match(capture))
							or (type(v) == "string" and (e == v or (e:match("%%") and v:match(e)))) then
							return true
						end --element type, equals string or capture in the strings element
					end --ke.table.inside({ 1, 2, "a4a" }, "%d[%.%d]*")
				end
				for _, v in pairs(self) do -- equals element
					if v == e then return true end
				end --ke.table.inside({1, 2, "a", "b", 3}, "string")
				return false
			end,
			
			index = function(self, e, capture)
				--returns the position or index of an element or element type in an array
				if type(e) == "table" then
					for k, v in pairs(self) do
						if ke.table.compare(v, e) then
							return k
						end
					end --if "e"(array) is inside an array
				elseif type(e) == "string" then
					for k, v in pairs(self) do
						if ke.table.type(v) == e
							or ((capture and type(v) == "string") and v:match(capture) == e:match(capture))
							or (type(v) == "string" and (e == v or (e:match("%%") and v:match(e)))) then
							return k
						end --element type, equals string or capture in the strings element
					end --ke.table.index({1, 2, "a4a"}, "%d[%.%d]*")
				end
				for k, v in pairs(self) do -- equals element
					if v == e then return k end
				end --ke.table.index({1, 2, "a", "b", 3}, "string")
				return false
			end,
			
			filter = function(self, support, idx)
				--filter the elements of the array by means of a function or element types
				local support = support or "number"
				local newself, i, newv = ke.table.clear(self), ke.math.count()
				local types = {"nil", "number", "string", "boolean", "table", "function", "thread", "userdata"}
				for k, v in pairs(self) do
					newv = v
					if support == "keys" or support == "values" then
						table.insert(newself, support == "keys" and k or v)
					else
						if type(support) == "string" then	
							if ke.table.inside(types, support) then
								newv = type(v) == support and v or nil
							end
						elseif type(support) == "function" then
							local TRUE, valor = pcall(support, k, v, self)
							if TRUE then
								newv = valor
							end
						end
						newself[k] = newv
					end
				end
				if idx then
					local keys = ke.table.filter(ke.table.filter(newself, "keys"), "number")
					table.sort(keys)
					local result = ke.table.clear(self)
					ke.table.recurse(function(k) table.insert(result, newself[k]) end, keys)
					for k, v in pairs(newself) do
						if type(k) == "string" then
							result[k] = v
						end
					end
					return result
				end
				return newself
			end, --ke.table.filter({1, 2, 3, "4", x = 5, 6, y = 9, [12] = 7}, "number", true)
			
			get = function(self, mode, support)
				--perform multiple operations with the array elements
				local self = type(self) == "function" and self() or self
				local mode, operation = mode or "suma"
				self = ke.table.new(self)
				operation = {
					["add"] = function(self, support)
						--sum the elements with a number or with the elements of an array
						local newtable, aux = ke.table.new(), support
						if type(aux) == "table" then
							for i = 1, #self do --ke.table.get({3, 3, 3, 3}, "add", {{1, 2}})
								newtable[i] = self[i] + (ke.table.type(aux) == "table" and aux[1][(i - 1) % #aux[1] + 1] or (aux[i] or 0))
							end --ke.table.get({3, 3, 3, 3}, "add", {1, 1})
						else
							local aux = type(aux) == "number" and aux or 0
							for i = 1, #self do
								newtable[i] = type(self[i]) == "table" and operation.add(self[i], aux) or self[i] + aux
							end
						end
						return newtable
					end, --ke.table.get({1, 2, {3, 4, 5}}, "add", 10)
					
					["average"] = function(self)
						--arithmetic average of the numbers in the array
						local _average, tbl_ave = 0, operation.toval(self)
						for i = 1, #self do
							_average = _average + tbl_ave[i]
						end
						return #self > 0 and _average / #self or 0
					end, --ke.table.get({10, 8, 9, 6}, "average")
					
					["combine"] = function(self, support)
						--combinations of n size of an array
						local newtable, n, newrow = ke.table.new(), ke.math.round(math.abs(type(support) == "number" and support or 2))
						local aux = ke.table.new(n)
						while true do
							newrow = ke.table.new(n, function(i) return self[aux[i]] end)
							newtable:insert(newrow)
							local i = n
							while aux[i] == #self - n + i do
								i = i - 1
							end
							if i < 1 then break end
							aux[i] = aux[i] + 1
							for k = i, n do
								aux[k] = aux[i] + k - i
							end
						end
						return newtable
					end, --ke.table.get({"a", "b", "c", "d"}, "combine", 2)
					
					["count"] = function(self, support)
						--number of times an element is inside, capture or an element type, in the array
						local n, e = 0, support
						local types = {"function", "table", "string", "color", "alpha", "shape", "clip", "number", "boolean", "point", "segment", "polygon"}
						if type(e) == "table" then
							for k, v in pairs(self) do
								n = ke.table.compare(v, e) and n + 1 or n
							end --si la tabla "e" está dentro de la tabla
						elseif type(e) == "string" then
							if ke.table.inside(types, e) then
								for k, v in pairs(self) do
									n = type(v) == "table" and n + operation.count(v, e) or n
									n = ke.table.type(v) == e and n + 1 or n
								end --tipo de elemento
							else
								for k, v in pairs(self) do
									n = type(v) == "table" and n + operation.count(v, e) or n
									if type(v) == "string" then --captura en los elementos strings
										n = v:match(e) and n + 1 or n
									elseif v == e then
										n = n + 1
									end --strings iguales
								end
							end
						else
							for k, v in pairs(self) do
								n = type(v) == "table" and n + operation.count(v, e) or n
								n = v == e and n + 1 or n
							end --elementos iguales
						end
						return n
					end, --ke.table.get({1, 2, "a", {"bar", 3, 7}, x = 0}, "count", "number")
					
					["delete"] = function(self, support)
						--remove the indicated elements from the array
						local newtable, Index, self2 = {}, {}, ke.table.copy(self)
						local retire_e = type(support) == "table" and support or {support}
						local types = {"function", "string", "color", "alpha", "shape", "clip", "number", "boolean", "point", "segment", "polygon"}
						for k, v in pairs(self2) do
							Index[#Index + 1] = type(k) == "number" and k or nil
							newtable[k] = type(v) == "table" and operation.delete(v, retire_e) or v
							for key, val in pairs(retire_e) do
								if type(val) == "table" and ke.table.type(val) == "number" then
									newtable[k] = not (type(k) == "number" and k >= val[1] and k <= (val[2] or val[1])) and v or nil
								elseif type(val) == "table" then --según su índice (pairs)
									for _, indx in pairs(val) do
										if k == indx then
											newtable[k] = nil
											break
										end --ke.table.get({"n", "b", {0, 9, "b", "c"}, 2, 7}, "delete", {{1, 3}})
									end --ke.table.get({1, x = 2, {"n", x = "m 0 0 l 80 80 ", 3}, "&HFF&", "&H0000FF&"}, "delete", {"a", {"x"}})
								else --ke.table.get({1, 2, "m 0 0 l 80 80 "}, "delete", "shape")
									if type(val) == "string" and ke.table.inside(types, val) then --según el tipo de elemento
										newtable[k] = ke.table.type(v) ~= val and newtable[k] or nil
									elseif v == val then --elimima los elementos en retire_e
										newtable[k] = nil
									end --ke.table.get({"m", 0, "b", {0, 9, "b", "c"}, 2, 7}, "delete", {"b", "a"})
								end
							end --ke.table.get({[9] = 9, [3] = 3, [4] = 4, [5] = 5, [6] = 6, x = {0, 0}}, "delete", {{4}})
						end --ke.table.get({"n", "b", {0, 9, "b", "c"}, 2, 7}, "delete", "b")
						Index = operation.org(Index)
						for i = 2, #Index do
							if Index[i] - Index[i - 1] ~= 1 then
								return newtable
							end
						end
						return operation.idx(newtable)
					end, --ke.table.get({"n", "b", "c"}, "delete", "b")
					
					["disorder"] = function(self)
						--randomly shuffles the content of an indexed array
						local newtable = ke.table.new(self)
						for i = #newtable, 2, -1 do
							local j = ke.math.rand(1, i)
							newtable[i], newtable[j] = newtable[j], newtable[i]
						end
						return newtable --ke.table.get(10, "disorder")
					end, --ke.table.get({"A", "B", "C", "D", "E"}, "disorder")
					
					["flatten"] = function(self)
						--returns a one-dimensional table
						local alis = ke.table.clear(self)
						ke.table.recurse(function(v) table.insert(alis, v) end, self)
						return alis
					end, --ke.table.get({[5] = "E", [2] = "B", x = 0, y = {[6] = "F", [3] = "C", [1] = "A"}}, "flatten")
					
					["idx"] = function(self, support)
						--organize by index the elements of the table and omit the nils
						local self = support and operation.toval(self) or self
						local newtable, index_num, index_key, key = ke.table.new(), {}, {}
						for k, v in pairs(self) do
							index_num[#index_num + 1] = type(k) == "number" and k or nil
							index_key[#index_key + 1] = type(k) ~= "number" and k or nil
						end
						index_num = operation.org(index_num)
						for i = 1, #index_num do
							key = index_num[i]
							newtable[#newtable + 1] = self[key]
						end
						for i = 1, #index_key do
							key = index_key[i]
							newtable[key] = self[key]
						end --ke.table.get({[5] = "E", [2] = "B", x = 0, y = {[6] = "F", [3] = "C", [1] = "A"}}, "idx")
						for k, v in pairs(newtable) do
							newtable[k] = type(v) == "table" and operation.idx(v) or v
						end
						return newtable
					end, --ke.table.get({1, [9] = 2, 3, 4, x = 0}, "idx")
					
					["inpack"] = function(self, support)
						--pack the array elements, into groups
						local parts = support or 2
						parts = type(support) == "table" and math.ceil(#self / support[1]) or parts
						local newtable = ke.table.new(math.ceil(#self / parts), {})
						for i = 1, math.ceil(#self / parts) do
							for k = 1, parts do
								newtable[i][k] = self[(i - 1) * parts + k]
							end
						end
						return newtable
					end, --ke.table.get(10, "inpack", 3)
					
					["insert"] = function(self, support)
						--insert "support" at the end of the array
						local newtable = ke.table.new(self)
						local support = type(support) == "table" and support or {support}
						for k, v in pairs(support) do
							k = type(k) == "number" and #newtable + 1 or k
							newtable[k] = v
						end --ke.table.get({1, 2, 3}, "insert", {"a", x = 8, 7})
						return newtable
					end,
					
					["inverse"] = function(self)
						--invert the position of the array elements
						local newtable, ini = ke.table.new(), self[0] and 0 or 1
						for k, v in pairs(self) do
							newtable[k] = type(k) == "number" and self[#self - k + ini] or v
						end
						return newtable
					end, --ke.table.get({1, 2, 3, 4, 5}, "inverse")
					
					["len"] = function(self)
						local n = 0
						for k, v in pairs(self) do
							n = n + 1
						end
						return n
					end,
					
					["max"] = function(self)
						--maximum array value
						local newtable = operation.org(self)
						return newtable[#newtable] and newtable[#newtable] or 0
					end, --ke.table.get({1, 3, 5, 7}, "max")
					
					["move"] = function(self, support)
						--shifts the indices of the array an integer number of positions
						local newtable = ke.table.new()
						local support = type(support) == "number" and math.ceil(math.abs(support)) or support or 0
						if type(support) == "number" then
							for k, v in pairs(self) do
								k = type(k) == "number" and k + support or k
								newtable[k] = v
							end --ke.table.get({1, 2, 3, 4, 5}, "move", 2)
						elseif type(support) == "table" and type(support[1]) == "number" then
							support = math.ceil(math.abs(support[1]))
							local n = #self
							for k, v in pairs(self) do
								newtable[k] = type(k) == "number" and self[1 + (support + k - 2) % n] or v
							end --ke.table.get({1, 2, 3, 4, 5, x = 0}, "move", {3})
						end
						return newtable
					end,
					
					["min"] = function(self)
						--minimum array value
						local newtable = operation.org(self)
						return newtable[1] and newtable[1] or 0
					end, --ke.table.get({1, 3, 5, 7}, "min")
					
					["newlen"] = function(self, support)
						--modify the array size using its own elements
						local newtable, n = ke.table.new(), support or #self
						if type(n) == "table" then
							local tbl1, tbl2 = ke.table.new(#self, math.floor(n[1] / #self)), ke.table.new(n[1] % #self, 1)
							local new_t = operation.add(tbl1, tbl2)
							for i = 1, #self do
								for k = 1, new_t[i] do
									newtable:insert(self[i])
								end
							end --ke.table.get({"a", "b", "c"}, "newlen", {5})
						elseif type(n) == "number" then
							newtable = ke.table.new(n, function(i) return self[(i - 1) % #self + 1] end)
						elseif type(tonumber(n)) == "number" then
							for i = 1, tonumber(n) do
								for k = 1, #self do
									newtable:insert(type(self[k]) == "function" and self[k]() or self[k])
								end
							end --ke.table.get({"a", "b", "c"}, "newlen", "2")
						end --ke.table.get({"a", "b", "c"}, "newlen", 5)
						return newtable
					end,
					
					["org"] = function(self, support)
						--returns the array with the numbers arranged in ascending order
						local newtable = operation.toval(self)
						local key = support or 1
						table.sort(newtable, function(a, b)
							a = type(a) == "table" and a[key] or a
							b = type(b) == "table" and b[key] or b
							return a < b end
						)
						return newtable
					end, --ke.table.get({4, 1, 3, {2, "x"}}, "org")
					
					["order"] = function(self)
						--arranges the elements of a string array in alphabetical order
						local newtable = ke.table.new(self)
						table.sort(newtable,
							function(a, b)
								local _, _, col1, num1 = tostring(a):find("^(.-)%s*(%d+)$")
								local _, _, col2, num2 = tostring(b):find("^(.-)%s*(%d+)$")
								if col1 and col2 and col1 == col2 then
									return tonumber(num1) < tonumber(num2)
								end
								return a < b
							end
						)
						return newtable
					end, --ke.table.get({"dog", "cat", "hen", "cow", "pig"}, "order")
					
					["outpack"] = function(self)
						--"unpacks" all the array contents into a single indexed array
						local function tbl_ipairs(self)
							local index, keys = {}, {}
							for k, v in pairs(self) do
								v = type(v) == "table" and tbl_ipairs(v) or v
								if type(k) ~= "number" then
									keys[#keys + 1], index[k], self[k] = k, v
								end
							end
							keys = operation.order(keys)
							for i = 1, #keys do
								self[#self + 1] = index[keys[i]] 
							end
							return self
						end
						local function tbl_unpack(tbl, self)
							for k, v in pairs(self) do
								tbl = type(v) == "table" and tbl_unpack(tbl, v) or tbl
								tbl[#tbl + 1] = type(v) ~= "table" and v or nil
							end
							return tbl
						end
						return tbl_unpack(ke.table.new(), tbl_ipairs(self))
					end, --ke.table.get({{x = 1, y = 2}, "7 8 ", 3, 4, x = 10, y = 11}, "outpack")
					
					["permute"] = function(self)
						--returns an array with the combinations of the elements
						local newtable = ke.table.new()
						local function output(per)
							local inside = {}
							for _, v in ipairs(per) do
								inside[#inside + 1] = v
							end
							newtable:insert(inside)
						end
						local function permutation(per, n)
							if n == 0 then
								output(per)
							else
								for i = 1, n do
									per[n], per[i] = per[i], per[n]
									permutation(per, n - 1)
									per[n], per[i] = per[i], per[n]
								end
							end
						end
						local n = #self
						permutation(self, n)
						return newtable
					end, --ke.table.get({1, 2, 3}, "permute")
					
					["pos"] = function(self, support)
						--returns an array with the positions of the element "e", of type, capture or equality
						local newtable, e = ke.table.new(), support
						local types = {"function", "table", "string", "color", "alpha", "shape", "clip", "number", "boolean", "point", "segment", "polygon"}
						if type(e) == "table" then
							for k, v in pairs(self) do
								newtable[#newtable + 1] = ke.table.compare(v, e) and k or nil
							end --si la tabla "e" está dentro de la tabla
						elseif type(e) == "string" then
							if ke.table.inside(types, e) then
								for k, v in pairs(self) do
									newtable[#newtable + 1] = type(v) == "table" and operation.pos(v, e) or (ke.table.type(v) == e and k or nil)
								end --tipo de elemento
							else
								for k, v in pairs(self) do
									newtable[#newtable + 1] = type(v) == "table" and operation.pos(v, e) or nil
									if type(v) == "string" then --captura en los elementos strings
										newtable[#newtable + 1] = v:match(e) and k or nil
									elseif v == e then
										newtable[#newtable + 1] = k
									end --strings iguales
								end --ke.table.get({1, 2, "box", {"b", 3, x = 0}}, "pos", "b")
							end
						else
							for k, v in pairs(self) do
								newtable[#newtable + 1] = type(v) == "table" and operation.pos(v, e) or (v == e and k or nil)
							end --elementos iguales
						end --ke.table.get({1, 2, "a", {"b", 3, x = 0}}, "pos", "number")
						return newtable
					end,
					
					["random"] = function(self)
						--returns a random element, never the same consecutive
						if #self <= 1 then
							return self[1]
						end
						local rand_e = self[ke.math.rand(#self)]
						while rand_e == RANDOM do
							rand_e = self[ke.math.rand(#self)]
						end
						RANDOM = rand_e
						return rand_e --ke.table.get(5, "random")
					end,
					
					["round"] = function(self, support)
						--returns the array with all the numbers rounded according to the third argument
						local newtable = ke.table.new(self)
						return ke.math.round(newtable, support)
					end,
					
					["string"] = function(self, support)
						--returns an array with the n-size parts of each string
						local n = type(support) == "function" and support() or support or 1
						local newtable = ke.table.new(self)
						for i, str in pairs(newtable) do
							if type(str) == "table" then
								newtable[i] = operation.string(str, n)
							elseif type(str) == "string" then
								local aux, chars, size = {}, {}, unicode.len(str)
								for c in unicode.chars(str) do
									table.insert(chars, c)
								end
								for j = 1, size, n do
									aux[#aux + 1] = ""
									for k = 1, n do
										aux[#aux] = aux[#aux] .. (chars[j + k - 1] or "")
									end
								end --ke.table.get({y = "line text", "pi", "demo", 453}, "string", 3)
								newtable[i] = n >= size and {str} or aux
							else
								newtable[i] = str
							end
						end
						return newtable
					end, --ke.table.get({"line text", "demo", "de"}, "string", 3)
					
					["subset"] = function(self, support)
						--returns a random subset of size n
						local n = type(support) == "function" and support() or support or ke.math.random(self.n)
						local self, newtable = self:get("disorder"), ke.table.new()
						n = math.abs(math.ceil(n))
						ke.table.iter(nil, function(i, v) newtable:insert(self[i]) end, {start = newtable, i = {1, n}})
						return newtable
					end, --ke.table.get(ke.text.char_lower, "subset", 4)
					
					["suma"] = function(self, support)
						--sum of elements from 1 to support or #self
						local sum, newtable = 0, operation.toval(self)
						local support = (support and support > #self) and #self or support or #self
						for i = 1, support do
							sum = sum + newtable[i]
						end
						return sum
					end, --ke.table.get({1, 2, "3", 4, 5}, "suma", 3)
					
					["tonumber"] = function(self)
						--convert elements to numbers, if possible
						local index = {}
						for k, v in pairs(self) do
							v = type(v) == "function" and v() or v
							self[k] = type(v) == "string" and ke.string.array(v, "number") or v
							v = type(v) == "table" and operation.tonumber(v) or v
							k = type(k) == "number" and #index + 1 or k
							index[k] = v
						end
						local function tbl_ipairs(self)
							local index, keys = {}, {}
							for k, v in pairs(self) do
								v = type(v) == "table" and tbl_ipairs(v) or v
								if type(k) ~= "number" then
									keys[#keys + 1], index[k], self[k] = k, v
								end
							end
							keys = operation.order(keys)
							for i = 1, #keys do
								self[#self + 1] = index[keys[i]] 
							end
							return self
						end
						local function tbl_unpack(tbl, self)
							for k, v in pairs(self) do
								tbl = type(v) == "table" and tbl_unpack(tbl, v) or tbl
								tbl[#tbl + 1] = type(v) ~= "table" and v or nil
							end
							return tbl
						end
						local newtable = tbl_unpack(ke.table.new(), tbl_ipairs(self))
						return newtable
					end, --ke.table.get({{x = 1, y = 2}, "7 8 ", 3, 4, x = 10, y = 11}, "tonumber")
					
					["topoint"] = function(self)
						--get the points of an array or a shape
						local values = operation.tonumber(self)
						local points = ke.table.new()
						for i = 1, #values, 2 do
							if values[i + 1] then
								points:insert(ke.shape.point.new(values[i], values[i + 1]))
							end
						end
						return points
					end, --ke.table.get(ke.shape.rectangle, "topoint")
					
					["tosegment"] = function(self)
						--get the line segments of an array or a shape
						local values = operation.tonumber(self)
						local segments = ke.table.new()
						for i = 1, #values - 3, 2 do
							segments:insert(ke.shape.segment.new({values[i], values[i + 1], values[i + 2], values[i + 3]}))
						end
						return segments
					end, --ke.table.get(ke.shape.rectangle, "tosegment")
					
					["toval"] = function(self)
						--assigns the actual value that each element represents
						local newtable, table_val = ke.table.new(), ke.table.copy(self)
						for k, v in pairs(table_val) do
							newtable[k] = (type(v) == "string" and v ~= "l") and ke.string.toval(v) or v
							newtable[k] = type(v) == "table" and operation.toval(v) or newtable[k]
						end --ke.table.get({"2", 4, {"5", "&HFF&"}, x = "7"}, "toval")
						return newtable
					end,
					
					["unique"] = function(self, support)
						--remove repeating elements from an indexed array
						local newtable, views = ke.table.new(), {}
						if support == "consecutive" then
							--remove only consecutive occurrences of each element
							newtable[1] = self[1]
							for i = 2, #self do
								newtable[#newtable + 1] = self[i] ~= newtable[#newtable] and self[i] or nil
							end --ke.table.get({1, 2, 2, 2, 5, 2, 2, 7, 7, 8}, "unique", true)
						elseif support == "last" then
							--remove all repeated elements from a table, except the last one
							for i = #self, 1, -1 do
								local val = self[i]
								if not views[val] then
									views[val] = true
									table.insert(newtable, 1, val)
								end
							end
						else--if not support or support == "first" then
							--remove all repeated elements from a table, except the first one
							for i = 1, #self do
								local val = self[i]
								if not views[val] then
									views[val] = true
									table.insert(newtable, val)
								end
							end
						end
						return newtable
					end, --ke.table.get({1, 2, 2, 2, 5, 6, 7, 7, 8}, "unique")
					
					["zip"] = function(self)
						--transposition of rows and columns in indexed tables
						local newtable, maxlen = {}, 0
						for _, subset in ipairs(self) do
							maxlen = math.max(#subset, maxlen)
						end
						for i = 1, maxlen do
							newtable[i] = {}
							for _, subset in ipairs(self) do
								table.insert(newtable[i], subset[i])
							end
						end
						return newtable
					end, --ke.table.get({{1, 2, 3}, {"a", "b", "c"}, {5, 6, 7, 8}}, "zip")
				}
				local self_op = operation[mode] and operation[mode](self, support) or self
				return self_op
			end,
			
			gsub = function(self, capture, filter)
				--generates replacements in the string elements of an array
				capture = type(capture) == "function" and capture() or capture or "KEfx"
				capture = type(capture) == "string" and {capture} or capture
				filter = filter or ""
				local newtable, _copy = ke.table.new(), ke.table.copy(self)
				for k, v in pairs(_copy) do
					for i = 1, #capture do
						v = type(v) == "string" and v:gsub(capture[i], filter) or v
					end
					newtable[k] = type(v) == "table" and ke.table.gsub(v, capture, filter) or v
				end --ke.table.gsub({"line demo", x = "string word fx"}, "o", "O")
				return newtable
			end,
			
			match = function(self, capture)
				--generates an array with the matches it finds, of equality, of type or of capture
				capture = type(capture) == "function" and capture() or capture or "KEfx"
				capture = type(capture) ~= "table" and {capture} or capture
				local newtable, _copy = ke.table.new(), ke.table.copy(self)
				local types = {"function", "table", "string", "color", "alpha", "shape", "clip", "number", "boolean", "point", "segment"}
				for i = 1, #capture do
					for k, v in pairs(_copy) do
						newtable[k] = ((ke.table.inside(types, capture[i]) and ke.table.type({v}) == capture[i])
						or (capture[i] == v) or (type(v) == "string" and type(capture[i]) == "string" and v:match(capture[i]))
						or ke.table.compare(v, capture[i])) and v or newtable[k]
						--si el elemento de la tabla es del mismo tipo que el indicado		--si la captura es el valor de un elemento en la tabla
						--si la tabla (capture[i]) es uno de los elementos de la tabla		--si el elemento es un string con la captura indicada
					end --ke.table.match({"a", "b", x = "c", [5] = 1, 2, {3}}, {"string", 1})
				end --ke.table.match({"a", "b", x = "c", [5] = 1, 2, 3}, "c")
				return newtable
			end,
			
			twin = function(self, ...)
				--create an array with the possible one-to-one matches, with the elements of the arrays entered
				local tables = ... and {...} or ke.table.copy(self)
				if ... then
					tables = #tables == 1 and ... or tables
					tables = ke.table.type(tables) ~= "table" and {tables} or tables
					table.insert(tables, 1, self)
				end
				local size_tbl = ke.table.new(#tables, function(i) return #tables[i] end)
				local min_size = ke.table.get(size_tbl, "min")
				local newtable = ke.table.new(min_size, {})
				for i = 1, min_size do
					for k = 1, #tables do
						newtable[i][k] = tables[k][i]
					end
				end
				return newtable
			end, --ke.table.twin({{1, 2, 3, 4}, {"A", "B", "C", "D"}, {7, 8, 9, 0, -1}})
			
		},
		
		string = {
			
			__name = "string",
			
			["__index"] = function(self, name)
				local newstring = ke.table.copy(string)
				table.insert(newstring, ke.string)
				return ke.string[name]
			end,
			
			["new"] = function(str)
				local str = type(str) == "function" and str() or str or ""
				if type(str) == "table" then
					return ke.table.recurse(ke.string.new, str)
				end
				local mt = getmetatable("").__index
				setmetatable(mt, ke.string)
				return str
			end,
			
			toval = function(self, vars, savestr)
				--converts a string to the value it represents
				local self = type(self) == "function" and self() or self or ""
				local data, sets = ke.infofx.data, ke.infofx.data.sets
				local env = {
					["ke"]	  = ke,			["fx"]	   = data.fx,		["j"]	 = j,			["getmetatable"] = _G.getmetatable,
					["xres"]  = xres,		["yres"]   = yres,			["maxj"] = maxj,		["setmetatable"] = _G.setmetatable,
					["ratio"] = ratio,		["pairs"]  = _G.pairs,		["char"] = sets.char,	["frame_dur"]	 = frame_dur,
					["table"] = _G.table,	["ipairs"] = _G.ipairs,		["syl"]  = sets.syl,	["tonumber"]	 = _G.tonumber,
					["type"]  = _G.type,	["string"] = _G.string,		["word"] = sets.word,	["tostring"]	 = _G.tostring,
					["math"]  = _G.math,	["var"]    = data.fx.var,	["line"] = sets.line,	["fxkara"]		 = data.fxkara,
				}
				for k, v in pairs(data.fx.var) do
					env[k] = v
				end
				if vars then --array
					for k, v in pairs(vars) do
						env[k] = v
					end --ke.string.toval({"0:00:02.018", "200"})
				end --ke.string.toval2("{3, 7, {x = 0, y = {5, 8}}}")
				local self = self:gsub("%d+:%d+:%d+%.%d+", function(HMS) return ke.time.HMS_to_ms(HMS) end)
				if savestr then --array
					for _, v in pairs(savestr) do
						self = self:gsub(v, "'<" .. "%1" .. ">'")
					end
				end
				local chunk, err = load(("return %s"):format(self), "= ke.string.toval", "t", env)
				self = self:gsub("'<", ""):gsub(">'", "")
				if not chunk then
					return self
				end --ke.string.toval("tonumber('3.5') + math.random(8)")
				local success, result = pcall(chunk)
				if result and type(result) == "table" then
					result = ke.table.new(result)
					result = ke.table.recurse(function(v)
						if type(v) == "string" then
							v = v:gsub("%b<>", function(cap) return cap:sub(2, -2) end)
						end
						return v
					end, result)
				end --ke.string.toval("{nada, 3, 7, {x = 0, y = {5, 8}}}", nil, {"nada"})
				return (success and result) and result or self
			end, --ke.string.toval("5 + xres")
			
			loadstr = function(str, vars)
				--converts a string to the value it represents
				local env = {ke = ke, _G = _G}
				ke.table.insert(env, vars, nil, true)
				local result, sent = {}, ""
				for statement in str:gmatch("([^;]+)") do
					table.insert(result, statement:match("^%s*(.-)%s*$"))
				end
				if #result > 0 then
					for i, stmt in ipairs(result) do
						local v = stmt:match("(%S+)[%s]*=[%s]*.+")
						sent = sent .. v .. " = " .. v .. "; "
					end
					sent = "{" .. sent .. "}"
				end
				local option3 = ("return function() %s return %s end"):format(str, sent)
				local chunk, err = load(option3, "ke.string.loadstr_chunk", "t", env)
				if not chunk then return str end
				local success, result = pcall(chunk)
				return (success and result) and result or str
			end, --ke.string.loadstr("x = 0; y = 9")()
			
			i = function(self)
				--converts the string "i" to a consecutive numeric value
				local self = type(self) == "function" and self() or self or ""
				if type(self) == "table" then
					return ke.table.recurse(ke.string.i, self)
				end --recurse
				local count_i = 0
				self = self:gsub("\\%w+%b()",
					function(capture)
						local new_cap = capture
						local capture = capture:gsub("([%+ %-%*%/%^%(%[%{%d%%]^*)i([%+ %-%*%/%^%)%]%}%%%\\]^*)",
							function(capture_ini, capture_fin)
								local cap_ini, cap_i, cap_fin = capture_ini, count_i, capture_fin
								return capture_ini:match("%d") and cap_ini .. " * " .. cap_i .. cap_fin or cap_ini .. cap_i .. cap_fin
							end
						)
						count_i = new_cap ~= capture and count_i + 1 or count_i
						return capture
					end
				)
				return ke.string.new(self)
			end, --ke.string.i("\\fr(-5i)\\frx(10 - i)")
			
			count = function(self, captures)
				--number of times a snapshot or snapshot family appears in a string
				local self = type(self) == "function" and self() or self or ""
				if type(self) == "table" then
					return ke.table.recurse(ke.string.count, self, captures)
				end --recurse
				captures = type(captures) == "function" and captures() or captures or "KEfx"
				captures = type(captures) ~= "table" and {captures} or captures
				local n = 0 --ke.string.count({"&HF58628&", "&HFF00FF&"}, "%x")
				for _, cap in ipairs(captures) do
					cap = cap == "number" and "%-?%d[%.%d]*"
					or (cap == "point" and "%-?%d[%.%d]*%s+%-?%d[%.%d]*")
					or (cap == "color" and "[%&%#Hh]^*%x%x%x%x%x%x[%&]*")
					or (cap == "alpha" and "%&[Hh]^*%x%x%&")
					or (cap == "shape" and "m%s+%-?%d[%.%-%d mlb]*") or cap
					for c in self:gmatch(cap) do
						n = n + 1
					end
				end --ke.string.count({"&HF58628&", "&HFF&"}, "%x")
				return n
			end, --ke.string.count("&HF58628&", "%x")
			
			array = function(self, captures)
				--returns an array with specific values of a string
				local self = type(self) == "function" and self() or self or ""
				if type(self) == "table" then
					return ke.table.recurse(ke.string.array, self, captures)
				end --recurse
				if not captures then
					return ke.table.new(unicode.chars(self), 1)
				end --"text" --> {"t", "e", "x", "t"}
				captures = type(captures) == "function" and captures() or captures or "KEfx"
				captures = type(captures) ~= "table" and {captures} or captures
				local result = ke.table.new()
				for _, cap in ipairs(captures) do
					cap = cap == "number" and "%-?%d[%.%d]*"
					or (cap == "color" and "[%&%#Hh]^*%x%x%x%x%x%x[%&]*")
					or (cap == "alpha" and "%&[Hh]^*%x%x%&")
					or (cap == "shape" and "m%s+%-?%d[%.%-%d mlb]*") or cap
					if cap == "chars" then
						result:insert(ke.table.new(unicode.chars(self), 1), nil, true)
					else --syl.text:array("chars")
						for A, B, C, D, E, F, G in self:gmatch(cap) do
							result:insert(ke.string.new(B and {A, B, C, D, E, F, G} or A))
						end --ke.string.array(ke.shape.circle, "(%-?%d[%.%d]*) (%-?%d[%.%d]*)")
					end
				end --ke.string.array("\\an5\\pos(600,320)\\blur4\\t(\\bord0)", "\\[%d]*%a+%b()", "\\[%d]*%a+%-?[%d&#]^*[%.%dH&%x]*")
				return result
			end,
			
			capture = function(self, captures, options)
				--makes special captures within a string
				local list, caps
				captures = type(captures) == "function" and captures() or captures or "KEfx"
				captures = type(captures) ~= "table" and {captures} or captures
				options = options or {}
				local overlap = options.overlap ~= false	-- true por defecto
				local advance = options.advance or 1		-- mínimo avance entre capturas
				if options.protect then
					list = type(options.protect) ~= "table" and {options.protect} or options.protect
					self, caps = ke.string.protect(self, list)
				end
				local pos, size = 1, unicode.len(self)
				local result, res = ke.table.new(), ke.table.new()
				for _, pattern in ipairs(captures) do
					while pos <= size do
						local ini, fin = self:find(pattern, pos)
						if ini then
							local cap = self:sub(ini, fin)
							if #result == 0 or not result[#result]:match(cap) then
								table.insert(result, ("<<%s>>"):format(ini) .. cap)
							end
							pos = overlap and ini + advance or fin + 1
						else
							break
						end --str = "\\frz-32\\blur-2\\1a&HFF&\\bordR(2,6)\\org(80,90)\\iclip(m 0 0 l 0 100 l 100 100 )\\t(0,80,\\1c&HFF00FF&)\\p1"
					end --ke.string.capture(str, {"\\[%d]*%a+%-?[%d&]^*[%.%dH%x&]*", "\\[%d]*[^t%W]%a+%b()"}, {protect = "\\t%b()", include = true})
					pos = 1
				end
				--ke.string.capture(str, {"\\[%d]*%a+%-?[%d&]^*[%.%dH%x&]*"}, {protect = "\\t%b()"})
				--str = "\\1a&HA4&\\frz-32\\blur-2\\1a&HFF&\\t(0,80,\\1c&HFF00FF&)"
				if list and options.include then
					local k = ke.math.count()
					self = self:gsub("<x>", function(cap) return caps[k()] end)
					pos = 1
					for _, pattern in ipairs(list) do
						while pos <= size do
							local ini, fin = self:find(pattern, pos)
							if ini then
								local cap = self:sub(ini, fin)
								if #result == 0 or not result[#result]:match(cap) then
									table.insert(result, ("<<%s>>"):format(ini) .. cap)
								end
								pos = overlap and ini + advance or fin + 1
							else
								break
							end
						end
						pos = 1
					end
				end
				for k, v in ipairs(result) do
					local idx = tonumber(v:match("<<(%d+)>>"))
					res[idx] = v:gsub("<<%d+>>", "")
				end
				return res("idx")
				--str = "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 "
				--ke.string.capture(str, "%d+ %d+ l %d+ %d+ ")
			end,
			
			protect = function(self, captures)
				--"protect" part of the string to apply replacement functions
				local self = type(self) == "function" and self() or self or ""
				if type(self) == "table" then
					return ke.table.recurse(ke.string.protect, self, captures)
				end --recurse
				captures = type(captures) == "function" and captures() or captures or "KEfx"
				captures = type(captures) == "string" and {captures} or captures
				local list = ke.table.new()
				local operation = function(str)
					local str = str
					:gsub("%%","%%%%"):gsub("%*", "%%*"):gsub("%+", "%%+"):gsub("%-", "%%-")
					:gsub("%(", "%%("):gsub("%)", "%%)"):gsub("%[", "%%["):gsub("%]", "%%]")
					return str
				end
				for _, cap in ipairs(captures) do
					self = self:gsub(cap,
						function(c)
							local key = self:find(operation(c))
							local Len = unicode.len(operation(c))
							list[key] = c
							return "€" .. string.rep("Æ", Len - 1)
						end
					)
				end
				self = self:gsub("€[Æ]*", "<x>")
				--	self, caps = ke.string.protect(self, captures)	--> protege las capturas en el string y genera la tabla de dichas capturas
				--	self = self:gsub(-todo-)						--> aplica los remplazos en el string protegido
				--	local k = ke.math.count()						--> contador para regresar las capturas salvadas al string protegido
				--	self = self:gsub("<x>", function(cap) return caps[k()] end)
				return ke.string.new(self), list("idx") --{ke.string.protect("foo(8)bar(0)demo6 foo(demo)", "%w+%b()")}
			end,
			
			delete = function(self, captures, except)
				--removes special captures within a string
				captures = type(captures) == "function" and captures() or captures or "KEfx2"
				captures = type(captures) ~= "table" and {captures} or captures
				except = type(except) == "function" and except() or except or -1
				except = type(except) ~= "table" and {except} or except
				if except.protect then
					local list, caps
					list = type(except.protect) ~= "table" and {except.protect} or except.protect
					self, caps = ke.string.protect(self, list)
				end
				for _, pattern in ipairs(captures) do
					local n, i, icaps = 0, 0, ke.table.new()
					self, n = self:gsub(pattern, function(c) icaps:insert(c) return "<0>" end)
					except[#except + 1] = except.last and n or nil
					if n > 0 then
						self = self:gsub("<0>", function(c) i = i + 1 return ke.table.inside(except, i) and icaps[i] or "" end)
					end
				end
				if except.protect then
					local k = ke.math.count()
					self = self:gsub("<x>", function(cap) return caps[k()] end)
				end
				return self
			end,
			
			change = function(self, captures, options)
				--change or remove a specific capture of a string
				local self = type(self) == "function" and self() or self or ""
				if type(self) == "table" then
					return ke.table.recurse(ke.string.change, self, captures, options)
				end --recurse
				local no_cap = {}
				local filter = options and options.filter or ""
				captures = type(captures) == "function" and captures() or captures or "KEfx"
				captures = type(captures) ~= "table" and {captures} or captures
				local nochange = options and options.nochange or {0}
				nochange = type(nochange) == "number" and {nochange} or nochange
				local protect = options and options.protect or nil
				if protect then --capturas protegidas
					self, no_cap = ke.string.protect(self, protect)
				end
				local aux = self
				local subself, tablecaps, n = {}, {}, 0
				local count = ke.math.count()
				for i, cap in ipairs(captures) do
					cap = ("(%s)"):format(cap)
					aux = aux:gsub(cap,
						function(todo)
							n = n + 1           
							table.insert(subself, todo)
							table.insert(tablecaps, ("<%s(%s)!"):format(n, i))
							return ("<%s(%s)!"):format(n, i)
						end
					)
				end
				for i, v in ipairs(nochange) do
					nochange[i] = v < 0 and n + v + 1 or v
				end
				for i, cap in ipairs(subself) do
					local k = tonumber(tablecaps[i]:match("%b()"):sub(2, -2))
					subself[i] = cap:gsub(captures[k],
						function(A, B, C, D, E, F, G, H, I, J, K, L)
							if ke.table.inside(nochange, count()) then
								return nil
							end
							return type(filter) == "table" and (type(filter[i]) == "function" and filter[i](A, B, C, D, E, F, G, H, I, J, K, L) or filter[i])
								or (type(filter) == "function" and filter(A, B, C, D, E, F, G, H, I, J, K, L) or filter)
						end
					)
				end
				self = aux:gsub("%b<!",
					function(cap)
						local i = tonumber(cap:match("%d+"))
						return subself[i]
					end
				) --ke.string.change("\\blur3\\t(\\blur1)", "(\\%l+)(%d+)", {filter = function(tag, val) return tag .. 2 * val end, protect = "\\t%b()"})
				if protect then --devuelve las capturas protegidas
					local k = ke.math.count()
					self = self:gsub("<x>", function(cap) return no_cap[k()] end)
				end --ke.string.change("foo(1)bar(2)foo(3)bar(4)\\t(\\demo1234)demo", "%w+%b()",{protect = {"foo%b()", "bar%b()"}})
				return ke.string.new(self)
			end, --ke.string.change("\\1c&H0000FF&\\t(\\1c&HFF00AA&)\\1c&H00FFFF&ru", "\\1c&H%x+&", {nochange = 1, protect = "\\t%b()"})
			
			parts = function(self, parts)
				--returns an array with the n-size parts of a string
				local self, parts = self or "", parts or 3
				if type(self) == "table" then
					return ke.table.recurse(ke.string.parts, self, parts)
				end --recurse
				parts = type(parts) == "number" and math.ceil(math.abs(parts)) or parts
				if type(parts) == "table" then
					parts[1] = parts[1] <= 0 and 1 or parts[1]
					parts[2] = parts[2] <= 0 and 2 or parts[2]
				end
				parts = parts == 0 and 2 or parts
				local chars_tbl, parts_tbl, Part_i, i = ke.string.array(self, "chars"), ke.table.new(), 0, 1
				while #chars_tbl > 0 do
					Part_i = type(parts) == "table" and ke.math.rand(parts[1], parts[2]) or parts
					parts_tbl[i] = ""
					for k = 1, Part_i do
						parts_tbl[i] = parts_tbl[i] .. (chars_tbl[1] or "")
						table.remove(chars_tbl, 1)
					end
					parts_tbl[i] = ke.string.new(parts_tbl[i])
					i = i + 1
				end --ke.string.parts("por ejemplo", 2) --> {"po", "r ", "ej", "em", "pl", "o"}
				return parts_tbl
			end,
			
			width = function(self, style)
				--string width according to the supplied style
				local self = self:gsub("%b{}", "")
				return aegisub.text_extents(style or ke.infofx.data.l.style, self)
			end, --ke.string.width(" ")
			
			disorder = function(self)
				--randomly scrambles the string
				local chars = ke.table.get(ke.string.array(self), "disorder")
				return ke.string.new(table.concat(chars))
			end, --ke.string.disorder("texto demo guía")
			
		},
		
		shape = {
			__name = "shape",
			
			-- internal predesigned shapes --
			circle		= "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 ",
			triangle	= "m 50 0 l 0 86 l 100 86 l 50 0 ",
			rectangle	= "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 ",
			pixel		= "m 0 0 l 0 1 1 1 1 0 ",
			heart		= "m 50 25 b 32 0 0 16 0 40 b 0 68 24 71 50 106 b 75 71 100 68 100 40 b 100 16 68 0 50 25 ",
			shine1t		= "m 0 0 l 47 50 l 0 100 l 50 53 l 100 100 l 53 50 l 100 0 l 50 47 m 42 50 b 42 61 58 61 58 50 b 58 39 42 39 42 50 ",
			shine2t		= "m 0 0 l 45 50 l 0 100 l 50 55 l 100 100 l 55 50 l 100 0 l 50 45 m 40 50 b 40 64 60 64 60 50 b 60 36 40 36 40 50 ",
			trebol		= "m 1 99 l 4 106 b 21 99 44 83 53 56 b 51 73 40 88 56 98 b 72 106 80 90 77 82 b 85 86 100 82 100 69 b 100 58 87 52 64 54 b 52 55 51 50 68 48 b 85 46 94 40 95 29 b 96 18 80 10 70 19 b 70 0 40 0 40 21 b 40 33 47 37 50 43 b 54 50 52 54 47 47 b 39 38 31 26 19 27 b 0 29 0 49 13 53 b 0 58 3 80 19 79 b 39 78 40 62 51 55 b 42 79 23 92 1 99 ",
			feather		= "m 0 0 b 0 20 10 28 27 34 b 10 33 47 49 54 55 b 62 62 72 77 78 75 l 80 78 l 90 79 b 94 86 96 94 97 100 l 100 100 b 99 93 96 84 93 78 b 100 56 88 41 73 30 l 73 39 l 69 28 b 62 24 55 23 49 19 l 48 24 l 45 19 b 31 10 13 12 0 0 m 91 74 l 88 75 b 79 49 57 40 46 35 b 22 25 8 15 2 5 b 11 17 22 23 48 34 b 64 41 82 51 91 74 ",
			bubble		= "m 50 100 b 78 100 100 78 100 50 b 100 22 78 0 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 m 50 1 b 79 1 99 21 99 50 b 99 76 80 93 68 96 b 62 98 66 94 50 94 b 34 94 38 98 32 96 b 20 93 1 78 1 50 b 1 22 22 1 50 1 m 88 22 b 79 11 75 14 85 24 b 92 38 94 33 88 22 m 12 15 b 12 19 18 19 18 15 b 18 11 12 11 12 15 m 14 16 l 15 30 l 16 16 l 30 15 l 16 14 l 15 0 l 14 14 l 0 15 m 50 94 b 63 94 61 100 52 100 b 42 100 38 94 50 94 ",
			star		= "m 38 36 l 0 36 l 31 59 l 20 95 l 50 72 l 81 94 l 69 59 l 100 36 l 62 36 l 50 0 l 38 36 ",
			sakura		= "m 50 40 l 35 0 b 10 10 0 32 0 61 b 0 88 15 117 50 130 b 85 117 100 88 100 61 b 100 32 90 10 65 0 l 50 40 ",
			test		= "m 0 0 l 0 100 l 100 100 l 100 0 l 0 0 m 20 20 l 80 20 l 80 80 l 20 80 l 20 20 m 40 40 l 40 60 l 60 60 l 60 40 l 40 40 ",
			
			-- subclass and sublibraries --
			["point"] = {	--subclass
				
				__name = "point",
				
				["__index"] = function(self, key)
					return ke.shape.point[key]
				end,
				
				["new"] = function(x, y, t)
					--create a new point
					local px, py, pt, p = x, y, t
					if type(x) == "string" and x:match("([blm]^*)%s+(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)") then
						pt, px, py = x:match("([blm]^*)%s+(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)")
					elseif type(x) == "table" then
						px, py, pt = x.x or x[1] or 0, x.y or x[2] or 0, x.t or x[3] or nil
					end
					p = ke.math.round({["x"] = px or 0, ["y"] = py or 0, ["t"] = pt}, ROUND_NUM)
					setmetatable(p, ke.shape.point)
					return p
				end, --ke.shape.point.new("m 12 -8.3")
				
				["__copy"] = function(self)
					return ke.shape.point.new(self.x, self.y, self.t)
				end,
				
				["__type"] = function(self)
					return "point"
				end,
				
				["__unm"] = function(self)
					return ke.shape.point.new(-self.x, -self.y, self.t)
				end,
				
				["__add"] = function(self, other)
					local addx, addy = ke.math.getpair(other, 0, 0)
					return ke.shape.point.new(self.x + addx, self.y + addy, self.t)
				end,
				
				["__sub"] = function(self, other)
					local subx, suby = ke.math.getpair(other, 0, 0)
					return ke.shape.point.new(self.x - subx, self.y - suby, self.t)
				end,
				
				["__div"] = function(self, other)
					other = type(other) == "number" and {other, other} or other
					local divx, divy = ke.math.getpair(other, 1)
					return ke.shape.point.new(self.x / divx, self.y / divy, self.t)
				end, --ke.shape.point.new(10, 10) / 2
				
				["__mul"] = function(self, other)
					if ke.table.type(other) == "matrix" then
						return ke.math.matrix.__mul(other, self)
					end
					return type(self) == "number" and ke.shape.point.new(self * other.x, self * other.y, other.t)
						or (type(other) == "number" and ke.shape.point.new(other * self.x, other * self.y, self.t)
						or self.x * other.x + self.y * other.y)
				end,
				
				["__lt"] = function(self, other)
					return self.x < other.x or (self.x == other.x and self.y < other.y)
				end,
				
				["__le"] = function(self, other)
					return self.x <= other.x and self.y <= other.y
				end,
				
				["__str"] = function(self)
					return ("%s %s "):format(self.x, self.y)
				end,
				
				["__eq"] = function(self, other)
					return math.abs(self.x - other.x) <= EPSILON and math.abs(self.y - other.y) <= EPSILON
				end,
				
				["__tostring"] = function(self)
					return ("(%s, %s)"):format(self.x, self.y)
				end,
				
				["len"] = function(self)
					--distance from the point to the origin
					return math.sqrt(self * self)
				end,
				
				["len2"] = function(self)
					--squart distance from the point to the origin
					return self * self
				end,
				
				["distance"] = function(self, other, ...)
					--linear distance between the point and all entered points
					return ke.math.distance(self, other, ...)
				end,
				
				["unpack"] = function(self, ...)
					--coordinates of the point and all points entered
					local others = {...}
					local coors = ke.table.new()
					coors:insert({self.x, self.y}, nil, true)
					ke.table.iter(others, function(i, p) coors:insert({p.x, p.y}, nil, true) end)
					return table.unpack(coors)
				end, --{ke.shape.point.unpack({x = 0, y = 0}, {x = 1, y = 1})}
				
				["middle"] = function(self, other)
					--midpoint between two points
					other = other or ke.shape.point.new(0, 0)
					return (self + other) / 2
				end,
				
				["ortho"] = function(self) --normal vector
					--perpendicular point with respect to the x-axis
					return ke.shape.point.new(-self.y, self.x) --normal
				end,
				
				["cross"] = function(self, other)
					--cross product between two points
					return self.x * other.y - self.y * other.x
				end,
				
				["dot"] = function(self, other)
					--dot product between two points
					return self.x * other.x + self.y * other.y
				end,
				
				["clockwise"] = function(self, other, third)
					--clockwise direction between three points
					return (other - self):cross(third - self) >= 0
				end,
				
				["collinear"] = function(self, other, third)
					--determines the collinearity between three points
					return math.abs((other - self):cross(third - self)) < EPSILON
				end,
				
				["angle"] = function(self, other, third)
					--angle between a point and the origin, or between two or three points
					if not other then
						return ke.math.angle(self)
					end
					local a1, a2 = ke.math.angle(self, other), ke.math.angle(other, third)
					local ang = third and 180 - a1 + a2 or a1
					return ang < 0 and ang + 360 or (ang > 360 and ang - 360 or ang)
				end,
				
				["bisector"] = function(self, other, third)
					--angle bisector of the angle formed by three points
					local a1, a2 = ke.math.angle(self, other), ke.math.angle(other, third)
					local ang = 180 - a1 + a2
					ang = ang < 0 and ang + 360 or (ang > 360 and ang - 360 or ang)
					ang = a1 + 180 + ang / 2
					return ang < 0 and ang + 360 or (ang > 360 and ang - 360 or ang)
				end, --ke.shape.point.bisector({x = 0, y = 0}, {x = 0, y = 10}, {x = 10, y = 10})
				
				["inline"] = function(self, line)
					--checks if a point belongs to a segment
					local ab, ap = line[1] - line[0], self - line[0]
					if math.abs(ap:cross(ab)) > EPSILON then return false end
					return ap:dot(ab) / ab:len2() --t
				end, --ke.shape.point.inline(ke.shape.point.new(1, 1), ke.shape.segment.new("0 0 l 4 4 "))
				
				["intriangle"] = function(self, p1, p2, p3)
					--determines if a point is inside a triangle defined by three points
					local v1, v2 = p2 - p1, p3 - p1
					local qp, dv = self - p1, v1:cross(v2)
					local l, m = qp:cross(v2) / dv, v1:cross(qp) / dv
					if l <= 0 or m <= 0 then
						return false
					end
					return l + m < 1
				end,
				
				["intersect"] = function(self, p1, p2, p3)
					--determines the intersection between two segments defined by four points
					local p0 = self
					local det = (p0.x - p1.x) * (p2.y - p3.y) - (p0.y - p1.y) * (p2.x - p3.x)
					if det == 0 then return nil end
					local t = ((p0.x - p2.x) * (p2.y - p3.y) - (p0.y - p2.y) * (p2.x - p3.x)) / det
					local u = -((p0.x - p1.x) * (p0.y - p2.y) - (p0.y - p1.y) * (p0.x - p2.x)) / det
					if t >= -EPSILON and t <= 1 + EPSILON and u >= -EPSILON and u <= 1 + EPSILON then
						return ke.shape.point.new({p0.x + t * (p1.x - p0.x), p0.y + t * (p1.y - p0.y)})
					end
					return nil
				end,
				
				["perpendicular"] = function(self, other, t, distance)
					--point perpendicular to two given points
					other = self == other and self:polar(self:angle() - 90, 32) or other
					t = t or 0.5
					local d = distance or 0
					local ax, ay, bx, by = self.x, self.y, other.x, other.y
					local vx, vy = bx - ax, by - ay
					local len = self:distance(other)
					d = type(d) == "table" and d[1] * len or d
					local px, py = ax + t * vx, ay + t * vy
					local nx, ny = -vy / len, vx / len
					return ke.shape.point.new({x = px + d * nx, y = py + d * ny, t = self.t})
				end, --ke.shape.point.perpendicular(ke.shape.point.new(4, 3), ke.shape.point.new(0, 0), 0.4, 5)
				
				["polar"] = function(self, angle, radius, ptype)
					--polar displacement of a point
					local x, y = ke.math.polar(angle, radius)
					return ke.shape.point.new(self.x + x, self.y + y, ptype or self.t)
				end,
				
				["topolar"] = function(self, other)
					--polar coordinates between two points
					other = other or ke.shape.point.new(0, 0)
					return self:angle(other), self:distance(other)
				end,
				
				["ratio"] = function(self, rxy)
					--scaling of the point by a given ratio
					local rx, ry = ke.math.getpair(rxy, 1)
					return ke.shape.point.new(self.x * rx, self.y * ry, self.t)
				end,
				
				["rotate"] = function(self, angle, o, axis)
					--rotation of a point about a given center
					self = type(self) == "function" and self() or self
					o = type(o) == "function" and o() or o or ke.shape.point.new(0, 0)
					local a = type(angle) == "function" and angle() or angle or 0
					a = type(a) == "table" and 360 - o:angle(self) + a[1] or a
					a = -math.rad(a)
					axis = axis or "z"
					local Px, Py, Pz = (self.x or 0) - o.x, (self.y or 0) - o.y, (self.z or 0) - (o.z or 0)
					local newrot = axis == "x" and ke.shape.point.new(Px + o.x, math.cos(a) * Py - math.sin(a) * Pz + o.y)
						or (axis == "y" and ke.shape.point.new(math.cos(a) * Px + math.sin(a) * Pz + o.x, Py + o.y))
						or ke.shape.point.new(math.cos(a) * Px - math.sin(a) * Py + o.x, math.sin(a) * Px + math.cos(a) * Py + o.y)
					newrot.t = self.t
					return newrot
				end, --ke.shape.point.new(10, 0):rotate(45)
				
				["distline"] = function(self, line)
					--distance and angle from a point to a line (segment)
					local angle = line:angle() + 90
					local x, y = ke.math.intersect({self, self:polar(angle, 1)}, line)
					return ke.math.distance(self, {x, y}), ke.math.angle(self, {x, y}), ke.shape.point.new(x, y)
				end, --ke.shape.point.distline(ke.shape.point.new(50, 50), ke.shape.segment.new({0, 50, 50, 0}))
				
				["rand"] = function(self, configs)
					--random point around a point, within a given range, or between two points
					--configs = {dx = val or table, dy = val or table, step = val, sign = true, n = positive_integer, distance = positive_integer}
					--configs = {other = point, rx = val, ry = val, step = val, n = positive_integer}
					--configs = {radius = val or table, step = val, n = positive_integer}
					self = self or ke.shape.point.new(0, 0)
					local st = type(configs) == "table" and configs.step or 1
					local sg = type(configs) == "table" and configs.sign or false
					if configs and configs.n then
						local n, mindistance = configs.n, configs.distance or 0
						configs.n, configs.distance = nil
						if mindistance <= 0 then
							return ke.table.new(n, function() return ke.shape.point.rand(self, configs) end)
						end
						local cellsize, nmax, rpoints, grid = mindistance, 100, {}, {}
						local function cellof(p)
							return math.floor(p.x / cellsize), math.floor(p.y / cellsize)
						end
						local function addtogrid(p)
							local cx, cy = cellof(p)
							grid[cx] = grid[cx] or {}
							grid[cx][cy] = grid[cx][cy] or {}
							table.insert(grid[cx][cy], p)
						end
						local function toclose(p)
							local cx, cy = cellof(p)
							for dx = -1, 1 do
								for dy = -1, 1 do
									local col = grid[cx + dx]
									local celda = col and col[cy + dy]
									if celda then
										for _, q in ipairs(celda) do
											local ddx, ddy = q.x - p.x, q.y - p.y
											if ddx * ddx + ddy * ddy < mindistance * mindistance then
												return true
											end
										end
									end
								end
							end
							return false
						end
						for i = 1, n do
							local insert = false
							for _ = 1, nmax do
								local p = ke.shape.point.rand(self, configs)
								if not toclose(p) then
									rpoints[#rpoints + 1] = p
									addtogrid(p)
									insert = true
									break
								end
							end
							if not insert then
								break
							end
						end --ke.shape.point.rand(nil, {dx = 60, dy = 60, n = 15, distance = 12})
						return rpoints
					end --recurse
					if configs and configs.radius then
						local angle = ke.math.rand(0, 360, 0.2)
						local radius = type(configs.radius) == "number" and {0, configs.radius} or configs.radius
						return self:polar(angle, ke.math.rand(radius[1], radius[2]))
					end --ke.shape.point.rand(nil, {radius = {10, 10}, n = 10, step = 0.4})
					if configs and configs.other then
						local angle, radius = self:topolar(configs.other)
						local rx = (type(configs) == "table" and configs.rx or 0.25) * radius
						local ry = (type(configs) == "table" and configs.ry or 0.50) * radius
						local a1, a2 = angle + 180 * ke.math.rand(2), angle + 90 * (-1) ^ ke.math.rand(2)
						local p1 = {ke.math.polar(a1, ke.math.rand(0, rx, st))}
						local p2 = {ke.math.polar(a2, ke.math.rand(0, ry, st))}
						return self:polar(angle, ke.math.rand(0, radius, st)) + p1 + p2
					end --ke.shape.point.rand(nil, {other = ke.shape.point.new(10, 10)})
					local dx = type(configs) == "table" and configs.dx or 256
					local dy = type(configs) == "table" and configs.dy or 256
					local rx = type(dx) == "table" and ke.math.rand(dx[1], dx[2], st, sg) or ke.math.rand(0, dx, st, sg)
					local ry = type(dy) == "table" and ke.math.rand(dy[1], dy[2], st, sg) or ke.math.rand(0, dy, st, sg)
					return self + {rx, ry}
				end, --ke.shape.point.rand(nil, {dx = 20, dy = 20, n = 5})
				
				["ipol"] = function(self, t, configs)
					--points interpolation
					local a = type(configs) == "table" and configs.accel or 1
					local s = type(configs) == "table" and configs.shape or nil
					local c = type(configs) == "table" and configs.curve or nil
					local o = type(configs) == "table" and configs.other or ke.shape.point.new(0, 0)
					local n = type(configs) == "table" and configs.n or nil
					t = t or 0
					local points = ke.table.new({self})
					if type(o) == "table" and o.__name == "point" then
						points:insert(o)
					elseif ke.table.type(o) == "point" then
						points:insert(o, nil, true)
					end
					local total = points.n
					local special = {
						["curve+"]  = {self:perpendicular(points[total], 0.33, {0.35}), self:perpendicular(points[total], 0.67, {0.35})},
						["curve-"]  = {self:perpendicular(points[total], 0.33, {-0.35}), self:perpendicular(points[total], 0.67, {-0.35})},
						["curve+-"] = {self:perpendicular(points[total], 0.33, {0.35}), self:perpendicular(points[total], 0.67, {-0.35})},
						["curve-+"] = {self:perpendicular(points[total], 0.33, {-0.35}), self:perpendicular(points[total], 0.67, {0.35})},
					}
					if c and special[c] then
						points:insert(special[c], 2, true)
					end
					local bernstein = function(i, n, u, t)
						local w = ke.math.normalize(u, a, s) * (t or 1)
						return (ke.math.factk(n) / (ke.math.factk(i) * ke.math.factk(n - i))) * (w ^ i) * ((1 - w) ^ (n - i))
					end
					local bn = points.n
					if not n then
						local x, y, val = 0, 0
						for i, p in ipairs(points) do
							val = bernstein(i - 1, bn - 1, t)
							x, y = x + p.x * val, y + p.y * val
						end
						return ke.shape.point.new(x, y, self.t)
					end
					if n < 2 then return self end
					local result = ke.table.new()
					for k = 1, n do
						local x, y, val = 0, 0
						for i, p in ipairs(points) do
							val = bernstein(i - 1, bn - 1, (k - 1) / (n - 1), t)
							x, y = x + p.x * val, y + p.y * val
						end
						result:insert(ke.shape.point.new(x, y, self.t))
					end --recurse
					return result --p1:ipol(0.5, {other = p2})
				end, --ke.shape.point.ipol(ke.shape.point.new(7, 7), 0.5)
				
				["reflect"] = function (self, p1, p2)
					--reflection of a point with respect to the segment indicated by two points
					local new = self:__copy()
					if not p2 or p1 == p2 then
						new = p1 * 2 - self
						return new
					end
					local v, w = p2 - p1, new - p1
					local norma2 = v.x ^ 2 + v.y ^ 2
					local t = (w.x * v.x + w.y * v.y) / norma2
					local aux = (v * t + p1) * 2 - new
					new.x, new.y = aux.x, aux.y
					return new
				end,
				
				-- points group functions --
				["group"] = function(points, filter, ...)
					--relevant information from a given group of points
					local minx, maxx, miny, maxy = math.huge, -math.huge, math.huge, -math.huge
					local xsum, ysum, cx, cy, lengths, total = 0, 0, {}, {}, {}, 0
					for i, p in ipairs(points) do
						minx, maxx = math.min(minx, p.x), math.max(maxx, p.x)
						miny, maxy = math.min(miny, p.y), math.max(maxy, p.y)
						table.insert(cx, p.x)
						table.insert(cy, p.y)
						xsum = xsum + p.x
						ysum = ysum + p.y
						if i > 1 then
							lengths[i - 1] = p:distance(points[i - 1])
							total = total + lengths[i - 1]
						end
					end
					local get = {
						rank = {x = maxx - minx, y = maxy - miny}, --width and height
						bounding = {minx, miny, maxx, maxy},
						n = #points,
						centroid = ke.shape.point.new(xsum / #points, ysum / #points),
						convex = ke.shape.point.toconvex(points),
						coors = {x = cx, y = cy},
						lengths = lengths
					}
					get.lengths.total = total
					if type(filter) == "string" then
						return get[filter] or points
					end
					for i, p in ipairs(points) do
						points[i] = filter(p, get, ...)
					end
					return points
				end, --ke.shape.point.group({{x = 1, y = 1}}, function(p, get, add) p.x = p.x + add[1] p.y = p.y + add[2] return p end, {5000, 1000})
				
				["sort"] = function(points, mode)
					--special organization of a group of points according to predetermined characteristics
					local centroid = ke.shape.point.group(points, "centroid")
					local n = #points
					local idxpoints = {}
					for i = 1, n do
						idxpoints[i] = {p = points[i], i = i}
					end
					local index = 1
					local function getindex(vertex, sortfunc)
						local best_item = vertex[1]
						local idx = 1
						for i = 2, #vertex do
							local current_item = vertex[i]
							if sortfunc(current_item, best_item) then
								best_item = current_item
								idx = i
							end
						end
						return idx
					end
					if type(mode) == "string" then
						local sorts = {
							["minx"] = function(a, b) return a.p.x < b.p.x end,
							["maxx"] = function(a, b) return a.p.x > b.p.x end,
							["miny"] = function(a, b) return a.p.y < b.p.y end,
							["maxy"] = function(a, b) return a.p.y > b.p.y end,
							["lefttop"] = function(a, b) --assdraw3 coors
								if a.p.y < b.p.y then return true end
								if a.p.y == b.p.y and a.p.x < b.p.x then return true end
								return false
							end,
							["righttop"] = function(a, b)
								if a.p.y < b.p.y then return true end
								if a.p.y == b.p.y and a.p.x > b.p.x then return true end
								return false
							end,
							["leftbottom"] = function(a, b)
								if a.p.y > b.p.y then return true end
								if a.p.y == b.p.y and a.p.x < b.p.x then return true end
								return false
							end,
							["rightbottom"] = function(a, b)
								if a.p.y > b.p.y then return true end
								if a.p.y == b.p.y and a.p.x > b.p.x then return true end
								return false
							end,
							["other"] = function(a, b) return true end
						}
						local sortfunc = sorts[mode] or sorts.other
						index = idxpoints[getindex(idxpoints, sortfunc)].i
					elseif type(mode) == "number" then --angle [0°, 360°)
						table.sort(idxpoints, function(a, b) return centroid:angle(a.p) < centroid:angle(b.p) end)
						local angle = mode
						local low, high, best = 1, n, -1
						local min_diff = math.huge
						while low <= high do
							local mid = math.floor((low + high) / 2)
							local current_item = idxpoints[mid]
							local current_angle = centroid:angle(current_item.p)
							local diff = math.abs(current_angle - angle)
							diff = math.min(diff, 360 - diff)
							if diff < min_diff then
								min_diff = diff
								best = mid
							end
							if current_angle < angle then
								low = mid + 1
							else
								high = mid - 1
							end
						end
						if best ~= -1 then
							local best_item = idxpoints[best]
							local best_angle = centroid:angle(best_item.p)
							local check_index = best
							while check_index > 1 do
								local prev_item = idxpoints[check_index - 1]
								local prev_angle = centroid:angle(prev_item.p)
								local prev_diff = math.abs(prev_angle - angle)
								prev_diff = math.min(prev_diff, 360 - prev_diff)
								if prev_diff < EPSILON then
									best = check_index - 1
								else
									break
								end
								check_index = check_index - 1
							end
						end
						index = best ~= -1 and idxpoints[best].i or 1
					elseif type(mode) == "function" then
						--[[ example: --más cerca al origen
						local compare_to_origin = function(item_a, item_b)
							local dist_a = math.sqrt(item_a.p.x^2 + item_a.p.y^2)
							local dist_b = math.sqrt(item_b.p.x^2 + item_b.p.y^2)
							return dist_a < dist_b
						end
						--]]
						index = idxpoints[getindex(idxpoints, mode)].i
					end
					local result = {}
					for i = 1, n do
						local current_original_index = (index + i - 2) % n + 1
						result[i] = points[current_original_index]
					end
					return result
				end,
				
				["toconvex"] = function(points)
					--maximum convex polygon obtained from a given group of points
					if #points < 3 then return points end
					local function cross3(o, a, b)
						return (a.x - o.x) * (b.y - o.y) - (a.y - o.y) * (b.x - o.x)
					end
					local pts = ke.table.copy(points)
					table.sort(pts, function(a, b) return math.abs(a.x - b.x) < EPSILON and a.y < b.y or a.x < b.x end)
					local uniques = {pts[1]}
					for i = 2, #pts do
						local last = uniques[#uniques]
						if pts[i] ~= last.x then
							table.insert(uniques, pts[i])
						end
					end
					pts = uniques
					if #pts < 3 then
						return pts
					end
					local inf, sup, envelope = {}, {}, {}
					for i = 1, #pts do
						while #inf >= 2 and cross3(inf[#inf - 1], inf[#inf], pts[i]) <= 0 do
							table.remove(inf)
						end
						table.insert(inf, pts[i])
					end
					for i = #pts, 1, -1 do
						while #sup >= 2 and cross3(sup[#sup - 1], sup[#sup], pts[i]) <= 0 do
							table.remove(sup)
						end
						table.insert(sup, pts[i])
					end
					table.remove(inf)
					table.remove(sup)
					for i = 1, #inf do
						table.insert(envelope, inf[i])
					end
					for i = 1, #sup do
						table.insert(envelope, sup[i])
					end
					return envelope
				end, --ke.shape.point.toconvex(ke.shape.point.rand(nil, {n = 25, dx = 50, dy = 50, sign = true}))
				
				["toshape"] = function(points)
					--shape in assDraw3 format obtained from a given group of points
					local shp = ("m %s %s l "):format(points[1].x, points[1].y)
					return ke.table.iter(nil, function(i, v, s) return s .. ("%s %s "):format(points[i].x, points[i].y) end, {start = shp, i = {2, #points}})
				end, --ke.shape.point.toshape(ke.shape.point.toconvex(ke.shape.point.rand(nil, {n = 25, dx = 50, dy = 50, sign = true})))
				
				["triangulate"] = function(points, rectangle, toshape)
					local result, delaunay, triangles = ke.table.new()
					delaunay = {
						orient2d = function(a, b, c)
							return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x)
						end, 
						incircumcircle = function(a, b, c, p)
							if delaunay.orient2d(a, b, c) < 0 then b, c = c, b end
							local ax, ay, bx, by, cx, cy = a.x - p.x, a.y - p.y, b.x - p.x, b.y - p.y, c.x - p.x, c.y - p.y
							local det = (ax * ax + ay * ay) * (bx * cy - cx * by) - (bx * bx + by * by) * (ax * cy - cx * ay) + (cx * cx + cy * cy) * (ax * by - bx * ay)
							return det > 0
						end,
						pointkey = function(p) return p.x .. "," .. p.y end,
						edgekey = function(p1, p2)
							local k1, k2 = delaunay.pointkey(p1), delaunay.pointkey(p2)
							return k1 < k2 and k1 .. "|" .. k2 or k2 .. "|" .. k1
						end,
						insertpoint = function(triangles, p)
							local bads, counter, news = {}, {}, {}
							for _, t in ipairs(triangles) do
								if delaunay.incircumcircle(t[1], t[2], t[3], p) then
									bads[#bads + 1] = t
								end
							end
							for _, t in ipairs(bads) do
								for _, a in ipairs({{t[1], t[2]}, {t[2], t[3]}, {t[3], t[1]}}) do
									local key = delaunay.edgekey(a[1], a[2])
									if counter[key] then
										counter[key].n = counter[key].n + 1
									else
										counter[key] = {n = 1, p1 = a[1], p2 = a[2]}
									end
								end
							end
							for _, t in ipairs(triangles) do
								local isbad = false
								for _, m in ipairs(bads) do
									if m == t then
										isbad = true
										break
									end
								end
								news[#news + 1] = not isbad and t or nil
							end
							for _, e in pairs(counter) do
								news[#news + 1] = e.n == 1 and {e.p1, e.p2, p} or nil
							end
							return news
						end
					}
					if rectangle then
						local r1, r2, r3, r4 = rectangle[1], rectangle[2], rectangle[3], rectangle[4]
						triangles = {{r1, r2, r3}, {r1, r3, r4}}
						for _, p in ipairs(points) do
							triangles = delaunay.insertpoint(triangles, p)
						end
					else
						local final, minx, miny, maxx, maxy = {}, math.huge, math.huge, -math.huge, -math.huge
						for _, p in ipairs(points) do
							minx, maxx = math.min(minx, p.x), math.max(maxx, p.x)
							miny, maxy = math.min(miny, p.y), math.max(maxy, p.y)
						end
						local d = math.max(maxx - minx, maxy - miny) * 10 + 1
						local s1, s2, s3 = {x = minx - d, y = miny - d}, {x = maxx + d * 2, y = miny - d}, {x = minx - d, y = maxy + d * 2}
						triangles = {{s1, s2, s3}}
						for _, p in ipairs(points) do
							triangles = delaunay.insertpoint(triangles, p)
						end
						for _, t in ipairs(triangles) do
							local touchsuper = false
							for _, v in ipairs(t) do
								if v == s1 or v == s2 or v == s3 then
									touchsuper = true
									break
								end
							end
							final[#final + 1] = not touchsuper and t or nil
						end
						triangles = final
					end
					ke.table.iter(triangles, function(i, v) result:insert(ke.table.copy(v)) end)
					result = toshape and result:filter(function(k, v) return ke.shape.point.toshape(v) end) or result
					return result --rect = {{x = 0, y = 0}, {x = 0, y = 60}, {x = 60, y = 60}, {x = 60, y = 0}}
				end, --ke.shape.point.triangulate(ke.shape.point.rand(nil, {dx = 60, dy = 60, n = 8}), rect, true)
				
			},
			
			["segment"] = {	--subclass
				
				__name = "segment",
				
				["__index"] = function(self, key)
					return ke.shape.segment[key]
				end,
				
				["new"] = function(seg)
					seg = ke.table.get(seg, "tonumber")
					local self = {t = #seg == 2 and "m" or (#seg == 4 and "l" or "b")}
					local i = self.t == "m" and 1 or 0
					for k = 1, #seg, 2 do
						self[i] = ke.shape.point.new(seg[k], seg[k + 1])
						i = i + 1
					end
					setmetatable(self, ke.shape.segment)
					return self
				end, --ke.shape.segment.new("0 0 b 1 1 2 2 3 3 ")
				
				["__copy"] = function(self)
					return ke.table.copy(self)
				end,
				
				["__type"] = function(self)
					return "segment"
				end,
				
				["__str"] = function(self)
					return tostring(self)
				end,
				
				["__tostring"] = function(self)
					local x0, y0, x1, y1 = self:unpack()
					local str = ("m %s %s "):format(x0, y0)
					local segstr = ("%s %s %s "):format(x0, y0, self.t)
					segstr = ke.table.iter(self, function(i, v, s) return s .. ("%s %s "):format(v.x, v.y) end, {start = segstr})
					return x1 and segstr or str
				end, --tostring(ke.shape.segment.cut(ke.shape.segment.new("m 0 0 b 15 0 30 0 45 0 "), {n = 4}))
				
				["__inv"] = function(self)
					--reverses the order of the points of a given segment
					return ke.shape.segment.new(ke.table.get(self, "inverse"))
				end, --ke.shape.segment.new("0 0 l 100 0 "):__inv()
				
				["length"] = function(self)
					--length of a given segment
					return self.t == "m" and 0 or ke.shape.beziers.length(self)
				end, --ke.shape.segment.new("0 20 b 20 0 40 0 60 20 "):length()
				
				["bezier"] = function(self, t)
					--point on a bezier curve according to a given parameter t
					if self.t == "m" then return self[1] end
					return ke.shape.beziers.config(self, t)
				end, --ke.shape.segment.new("0 20 b 20 0 40 0 60 20 "):bezier(0.25)
				
				["to_bezier"] = function(self)
					--converted line to bezier
					if self.t == "l" then --line
						local x0, y0, x3, y3 = self:unpack()
						self = {t = "b", --bezier
							[0] = {x = x0, y = y0},
							[1] = {x = x0 + 0.33 * (x3 - x0), y = y0 + 0.33 * (y3 - y0)},
							[2] = {x = x0 + 0.67 * (x3 - x0), y = y0 + 0.67 * (y3 - y0)},
							[3] = {x = x3, y = y3}
						}
						self = ke.shape.segment.new(self)
					end
					return self
				end, --ke.shape.segment.new("0 0 l 0 100 "):to_bezier()
				
				["unpack"] = function(self, inpoints)
					if inpoints then
						return table.unpack(ke.table.get(self, "topoint"))
					end
					return table.unpack(ke.table.get(self, "tonumber"))
				end,
				
				["inside"] = function(self, p)
					--check point are inside in segment
					if self.t == "l" then
						local t = p:inline(self)
						return ke.math.between(t, 0, 1) and t or false
					end
					return self.t == "b" and ke.shape.beziers.inside(self, p) or false
				end, --ke.shape.segment.inside(ke.shape.segment.new("m 0 20 b 20 0 40 0 60 20 "), ke.shape.point.new("l 30 5 "))
				
				["cut"] = function(self, t)
					--divides a segment into parts according to a given parameter t
					if type(t) == "table" then
						local parts = ke.table.new()
						local ts = t.t and ke.math.normalize({t = t.t}) or nil
						ts = t.n and ke.table.new(t.n - 1, function(i) return i / t.n end) or ts
						if t.random then
							local tn = type(t.random) == "table" and ke.math.rand(t.random[1], t.random[2]) or t.random
							ts = ke.table.new(tn - 1, function() return ke.math.rand(0.05, 0.95, 0.001) end)
							table.sort(ts)
						end --ke.shape.segment.cut(ke.shape.segment.new("m 0 0 l 100 0 "), {n = 4})
						ts = ke.math.normalize({t = ts})
						local n = #ts
						if n == 1 then return self end
						local cur = self
						for i = 1, n do
							if ts[i] > 0 and ts[i] < 1 then
								local left, right = ke.shape.segment.cut(cur, ts[i])
								parts[i], cur = left, right
							end
						end --ke.shape.segment.cut(ke.shape.segment.new("m 0 0 l 100 0 "), {random = 4})
						parts:insert(cur)
						local newself = parts[1]
						for i = 2, #parts do
							for k = 1, 3 do
								table.insert(newself, parts[i][k])
							end
						end
						return newself
					end
					if self.t == "m" then
						return self
					end
					local x0, y0, x2, y2 = self:unpack()
					local x1, y1 = x0 + t * (x2 - x0), y0 + t * (y2 - y0)
					local s1, s2 = {x0, y0, x1, y1}, {x1, y1, x2, y2}
					local x, y = x1, y1
					if self.t == "b" then
						local Sx0, Sy0, Sx1, Sy1, Sx2, Sy2, Sx3, Sy3 = self:unpack()
						local bx0, by0 = Sx0 * (1 - t) + Sx1 * t, Sy0 * (1 - t) + Sy1 * t
						local bx1, by1 = Sx1 * (1 - t) + Sx2 * t, Sy1 * (1 - t) + Sy2 * t
						local bx2, by2 = Sx2 * (1 - t) + Sx3 * t, Sy2 * (1 - t) + Sy3 * t
						local bx3, by3 = bx0 * (1 - t) + bx1 * t, by0 * (1 - t) + by1 * t
						local bx4, by4 = bx1 * (1 - t) + bx2 * t, by1 * (1 - t) + by2 * t
						local bx5, by5 = bx3 * (1 - t) + bx4 * t, by3 * (1 - t) + by4 * t
						s1, s2 = {Sx0, Sy0, bx0, by0, bx3, by3, bx5, by5}, {bx5, by5, bx4, by4, bx2, by2, Sx3, Sy3}
						x, y = bx5, by5
					end
					return ke.shape.segment.new(s1), ke.shape.segment.new(s2), ke.shape.point.new(x, y)
				end,
				
				["intersect"] = function(self, other, without_vertices)
					--intersection (if any) between two segments
					local s1, s2 = ke.shape.segment.new(self), ke.shape.segment.new(other)
					local x, y, t = ke.math.intersect(s1, s2)
					local a, b, s = ke.math.intersect(s2, s1)
					if s1.t == "l" and s2.t == "l" then --segment and segment
						if without_vertices then
							if (t and (t <= 0 or t >= 1)) or (s and (s <= 0 or s >= 1))
								or math.abs(s1:angle() - s2:angle()) == 180 or s1:angle() == s2:angle() then
								return false
							end --ke.shape.segment.intersect("0 0 l 12 15 ", "5 0 l -4 5 ")
						else
							if (t and (t < 0 or t > 1)) or (s and (s < 0 or s > 1))
								or math.abs(s1:angle() - s2:angle()) == 180 or s1:angle() == s2:angle() then
								return false
							end
						end
						return ke.shape.point.new(x, y), t, s
					elseif s1.t == "l" or s2.t == "l" then --segment and bezier
						local seg = s1.t == "l" and s1 or s2
						local bez = s1.t == "l" and s2 or s1
						local segs = bez:split(1)
						local parts = ke.table.new(#segs, function(i) return ke.shape.segment.new({segs[i - 1], segs[i]}) end)
						local result = {}
						for _, s in ipairs(parts) do
							local p, t, u = seg:intersect(s)
							if p then
								table.insert(result, {p, t = t, u = u})
							end
							if #result == 3 then break end
						end --ke.shape.segment.intersect("m -5 25 l 57 3 ", "m 15 2 b 12 47 32 -7 45 13 ")
						return #result > 0 and result or false
					end
					return false
				end,
				
				["angle"] = function(self, other)
					--angle segment line or angle between two segments line
					return self.t == "m" and 0 or (other and self[0]:angle(self[1], other[1]) or ke.math.angle(self))
				end,
				
				["bisector"] = function(self, other)
					--mid angle between two segments line
					local ang = self:angle() - 180 + 0.5 * self:angle(other)
					return ang < 0 and ang + 360 or (ang > 360 and ang - 360 or ang)
				end,
				
				["parameter"] = function(self, t)
					--point and angle corresponding to a parameter t of a given segment
					if self.t == "m" then return self end
					t = type(t) == "table" and ke.shape.beziers.length2t(self, t[1]) or tonumber(t)
					local point, angle = self:bezier(t)
					return point, angle, t
				end, --ke.shape.segment.new("0 20 b 20 0 40 0 60 20 "):parameter(0.25)
				
				["split"] = function(self, split)
					--redraws the segment into straight segments of given length
					split = type(split) == "function" and split() or split or 2
					local segms = type(split) == "table" and split[1] or nil
					local seg = self:__copy()
					if self.t == "m" then
						return self
					elseif self.t == "l" then
						local angle, length = self[0]:angle(self[1]), self[0]:distance(self[1])
						local parts = segms and length / segms or length / ke.math.round(length / split)
						for k = 1, ke.math.round(length / parts) do
							seg[k] = self[0]:polar(angle, parts * k)
						end
					else
						seg.t = "l"
						local l, k, t = self:length(), 1, 0
						split = segms and l / segms or split
						while true do
							t = ke.shape.beziers.length2t(self, k * split)
							if not t or t > 1 then
								local p = self:bezier(1)
								table.insert(seg, p)
								break
							end
							seg[k] = self:bezier(t)
							k = k + 1
						end
					end
					return seg
				end, --ke.shape.segment.split(ke.shape.segment.new("m 0 0 l 10 0 "), {4})
				
				["intax"] = function(self, other)
					--check if two segments are "overlapping"
					local s1, s2 = ke.shape.segment.new(self), ke.shape.segment.new(other)
					local a1, a2 = s1:angle(), s2:angle()
					if (s1[0] == s2[0] and math.abs(a1 - a2) == 180) or (s1[0] == s2[1] and a1 == a2)
						or (s1[1] == s2[1] and math.abs(a1 - a2) == 180) or (s1[1] == s2[0] and a1 == a2) then
						return false
					end
					if not s1:intersect(s2) then
						local a1, a2 = ke.shape.segment.angle(s1), ke.shape.segment.angle(s2)
						local x0, y0, x1, y1 = table.unpack(ke.table.get(s1, "tonumber"))
						local x2, y2, x3, y3 = table.unpack(ke.table.get(s2, "tonumber"))
						if     (x0 > x2 and x0 > x3) and (x1 > x2 and x1 > x3) or (x0 < x2 and x0 < x3) and (x1 < x2 and x1 < x3)
							or (y0 > y2 and y0 > y3) and (y1 > y2 and y1 > y3) or (y0 < y2 and y0 < y3) and (y1 < y2 and y1 < y3) then
							return false
						end
						return (a1 == a2 or math.abs(a1 - a2) == 180) and true or false
					end
					return false
				end,
				
				["rotate"] = function(self, angle, o)
					--rotation of the segment about a given angle and center
					local org = o == 0 and self[0] or (o == 1 and self[1] or o)
					for k, v in pairs(self) do
						self[k] = type(k) == "number" and ke.shape.point.rotate(v, angle, org) or v
					end
					return ke.shape.segment.new(self)
				end, --ke.shape.segment.new("0 5 l 100 5 "):rotate(45)
				
				["extend"] = function(self, ext_i, ext_f)
					--extension of the segment according to a given length
					local self = self:__copy()
					local ext_i, ext_f, a = ext_i or 0, ext_f or 0, self:angle()
					self[0], self[1] = self[0]:polar(a + 180, ext_i), self[1]:polar(a, ext_f)
					return self
				end,
				
				["move"] = function(self, dxy)
					--displacement of the segment on the cartesian plane
					local dx, dy = ke.math.getpair(dxy, 0, 0)
					local k = self.t == "m" and 1 or 0
					for i = k, #self do
						self[i] = self[i] + {dx, dy}
					end
					return ke.shape.segment.new(self)
				end, --ke.shape.segment.new("0 0 b 2 2 4 4 6 6 "):move({-3,0})
				
				["ratio"] = function(self, rxy)
					--scaling of the segment by a given ratio
					local rx, ry = ke.math.getpair(rxy, 1)
					local k = self.t == "m" and 1 or 0
					for i = k, #self do
						self[i].x = self[i].x * rx
						self[i].y = self[i].y * ry
					end
					return ke.shape.segment.new(self)
				end, --ke.shape.segment.new("0 0 b 2 2 4 4 6 6 "):ratio({2,1})
				
			},
			
			["beziers"] = {	--sublibrary
				
				["config"] = function(points, t)
					--curve bezier points, and angle
					t = type(t) == "function" and t() or t or 0
					points = ke.table.get(points, "topoint")
					local n, count = #points - 1, #points
					local bzr = ke.table.copy(points)
					while count > 1 do
						for i = 1, count - 1 do
							bzr[i] = bzr[i] * (1 - t) + bzr[i + 1] * t
						end
						count = count - 1
					end
					local point = bzr[1]
					local vec = ke.shape.beziers.derivative(points, t)
					local angle = math.deg(math.atan2(-vec.y, vec.x))
					return point, angle
				end, --ke.shape.beziers.config("m 0 20 b 20 0 40 0 60 20 ", 0.25)
				
				["length"] = function(bezier, t, n)
					--cubic bezier curve length
					t, n = t or 1, n or 8
					local coor = ke.table.get(bezier, "tonumber")
					if #coor == 4 then return ke.math.distance(coor) * t end
					local differential = function(xybzr, t)
						local difpos = {}
						difpos[1] = {
							[1] = xybzr[4][1] * t ^ 3 + 3 * xybzr[3][1] * t ^ 2 + 3 * xybzr[2][1] * t + xybzr[1][1],
							[2] = xybzr[4][2] * t ^ 3 + 3 * xybzr[3][2] * t ^ 2 + 3 * xybzr[2][2] * t + xybzr[1][2]
						}
						difpos[2] = {
							[1] = 3 * (xybzr[4][1] * t ^ 2 + 2 * xybzr[3][1] * t + xybzr[2][1]),
							[2] = 3 * (xybzr[4][2] * t ^ 2 + 2 * xybzr[3][2] * t + xybzr[2][2])
						}
						difpos[3] = {
							[1] = 6 * (xybzr[4][1] * t + xybzr[3][1]),
							[2] = 6 * (xybzr[4][2] * t + xybzr[3][2])
						}
						return difpos
					end
					local dt, ct1, ct2 = {}, 0, 0
					for i = 1, 2 * n + 1 do
						dt[i] = (i - 1) * t / (2 * n)
					end
					local difvec, dxbezier = {}, {}
					difvec[1] = {bezier[1].x - bezier[0].x, bezier[1].y - bezier[0].y}
					difvec[2] = {bezier[2].x - bezier[1].x, bezier[2].y - bezier[1].y}
					difvec[3] = {bezier[3].x - bezier[2].x, bezier[3].y - bezier[2].y}
					difvec[4] = {difvec[2][1] - difvec[1][1], difvec[2][2] - difvec[1][2]}
					difvec[5] = {difvec[3][1] - difvec[2][1], difvec[3][2] - difvec[2][2]}
					difvec[6] = {difvec[5][1] - difvec[4][1], difvec[5][2] - difvec[4][2]}
					dxbezier[1] = {bezier[0].x, bezier[0].y}
					dxbezier[2] = {difvec[1][1], difvec[1][2]}
					dxbezier[3] = {difvec[4][1], difvec[4][2]}
					dxbezier[4] = {difvec[6][1], difvec[6][2]}
					local difpos = differential(dxbezier, dt[1])
					local phyt1 = (difpos[2][1] ^ 2 + difpos[2][2] ^ 2) ^ 0.5
					difpos = differential(dxbezier, dt[2 * n + 1])
					local phyt2 = (difpos[2][1] ^ 2 + difpos[2][2] ^ 2) ^ 0.5
					for i = 1, n do
						difpos = differential(dxbezier, dt[2 * i])
						ct1 = ct1 + (difpos[2][1] ^ 2 + difpos[2][2] ^ 2) ^ 0.5
					end
					for i = 1, n - 1 do
						difpos = differential(dxbezier, dt[2 * i + 1])
						ct2 = ct2 + (difpos[2][1] ^ 2 + difpos[2][2] ^ 2) ^ 0.5
					end
					return (t / (6 * n)) * ((phyt1 + phyt2) + (4 * ct1) + (2 * ct2))
				end, --ke.shape.beziers.length(ke.shape.segment.new("0 20 b 20 0 40 0 60 20 "))
				
				["derivative"] = function(bezier, t)
					--calculate the Bezier curve derivative
					local points = ke.table.get(bezier, "topoint")
					local n, der = points.n - 1, {}
					for i = 1, n do
						der[i] = n * (points[i + 1] - points[i])
					end
					if not t then return der end
					local count = #der
					while count > 1 do
						for i = 1, count - 1 do
							der[i] = der[i] * (1 - t) + der[i + 1] * t
						end
						count = count - 1
					end
					return der[1]
				end, --ke.shape.beziers.derivative("m 0 20 b 20 0 40 0 60 20 ")
				
				["length2t"] = function(bezier, length)
					local len1, t, i = length, 1, 1
					local len2 = ke.shape.beziers.length(bezier, t)
					if len1 > len2 then return false end
					local coor = ke.table.get(bezier, "tonumber")
					if #coor == 4 then return length / ke.math.distance(coor) end
					while not ke.math.equality(len1, len2, 5) do
						t = t + (len2 < len1 and 1 or -1) * (1 / (2 ^ i))
						len2 = ke.shape.beziers.length(bezier, t)
						i = i + 1
					end
					return t
				end, --ke.shape.beziers.length2t(ke.shape.segment.new("0 20 b 20 0 40 0 60 20 "), 34.434)
				
				["length2seg"] = function(shp, length)
					local offset, segs, seg, target_length = {[0] = 0}, shp:__seg()
					for i, s in ipairs(segs) do
						offset[i] = offset[i - 1] + s:length()
					end
					local length = math.abs(offset[#offset] - length) < 1 and offset[#offset] or length
					for i = 1, #offset - 1 do
						if length >= offset[i] and length <= offset[i + 1] then
							seg, target_length = segs[i + 1], length - offset[i]
							return seg, target_length
						end
					end
					return false
				end, --{ke.shape.beziers.length2seg(ke.shape.new(ke.shape.rectangle), 40)}
				
				["coefficients"] = function(bezier)
					local points = ke.table.get(bezier, "topoint")
					local n = points.n - 1
					local cx, cy = ke.table.new(n + 1, 0), ke.table.new(n + 1, 0)
					local binomial = function(n, k)
						if k > n then return 0 end
						local r = 1
						for i = 1, k do
							r = r * (n - i + 1) / i
						end
						return r
					end
					for i = 0, n do
						for j = 0, n - i do
							local k = i + j + 1
							local coeff = binomial(n, i) * binomial(n - i, j) * (j % 2 == 0 and 1 or -1)
							cx[k] = cx[k] + points[i + 1].x * coeff
							cy[k] = cy[k] + points[i + 1].y * coeff
						end
					end
					return cx, cy
				end, --ke.shape.beziers.coefficients("m 0 20 b 20 0 40 0 60 20 ")
				
				["inside"] = function(bezier, p)
					bezier = ke.shape.segment.new(bezier)
					cx, cy = ke.shape.beziers.coefficients(bezier)
					cx[1] = cx[1] - p.x
					local roots = ke.math.equation(cx, true)
					for _, t in ipairs(roots) do
						if ke.math.between(t, -1e-3, 1 + 1e-3) then
							t = ke.math.clamp(t)
							local yval = ke.math.evaluate(cy, t)
							if math.abs(yval - p.y) < 1e-3 then
								return t
							end
						end
					end
					return false
				end, --ke.shape.beziers.inside("m 0 20 b 20 0 40 0 60 20 ", {x = 30, y = 5})
				
				["roots"] = function(bezier)
					local cx, cy = ke.shape.beziers.coefficients(bezier)
					local xroots, yroots = ke.math.equation(cx, 1), ke.math.equation(cy, 1)
					xroots = xroots:filter(function(k, v) return (v >= 0 - EPSILON and v <= 1 + EPSILON) and v or nil end)
					yroots = yroots:filter(function(k, v) return (v >= 0 - EPSILON and v <= 1 + EPSILON) and v or nil end)
					return xroots, yroots
				end, --{ke.shape.beziers.roots("m 7 7 b 11 -44 48 56 65 -31 ")}
				
				["pos"] = function(points, n)
					local fx = ke.infofx.data.fx
					local first = table.remove(points)
					local bzrs = ke.recall.memory.pnts or ke.recall.remember("pnts", first:ipol(1, {n = n, other = points}))
					ke.recall.maxloop(n)
					local p = bzrs[ke.infofx.data.j]
					return ("\\pos(%s,%s)"):format(fx.center + p.x, fx.middle + p.y)
				end, --ke.shape.beziers.pos(ke.shape.point.rand(nil, {dx = 20, dy = 20, n = 5}), 20)
				
			},
			
			["clipper"] = { --sublibrary
				
				topaths = function(paths)
					--get points from shape
					paths = ke.shape.__init(paths)
					local shapes, clockwise = {}, false
					for i, s in ipairs(paths) do
						if i == 1 and s:isclockwise() then
							clockwise = true
						end
						table.insert(shapes, clockwise and s:__inv().code or s.code)
					end
					paths = ke.shape.new(table.concat(shapes))
					paths = paths:redraw(2, "bezier")
					local points = {}
					for i, s in ipairs(paths) do
						points[i] = {}
						local k = 1
						for x, y in s.code:gmatch("(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)") do
							points[i][k] = {x = tonumber(x) * SCALE_PATHS, y = tonumber(y) * SCALE_PATHS}
							k = k + 1
						end
					end
					return points
				end,
				
				toshape = function(paths)
					--converts the paths struct to shape
					local codes = {}
					for i, path in ipairs(paths) do
						local asscode = ""
						for _, p in ipairs(path) do
							asscode = asscode .. ("l %s %s "):format(p.x / SCALE_PATHS, p.y / SCALE_PATHS)
						end
						codes[i] = asscode:gsub("l", "m", 1)
					end
					local code = table.concat(codes)
					return ke.shape.new(code):__closed()
				end,
				
				boolean = function(subject, clip, operation, filltype)
					--boolean operations between two shapes
					local CPP = include("kelibs\\clipper.lua")
					subject = ke.shape.clipper.topaths(subject)
					clip = ke.shape.clipper.topaths(clip)
					local cpp = CPP.Clipper()
					cpp:AddPaths(subject, CPP.ClipperLib.PolyType.ptSubject, true)
					cpp:AddPaths(clip, CPP.ClipperLib.PolyType.ptClip, true)
					local ClipType = {
						["intersection"] = 0;
						["union"] = 1;
						["difference"] = 2;
						["xor"] = 3;
					}
					local FillType = {
						["evenodd"] = 0;
						["nonzero"] = 1;
						["positive"] = 2;
						["negative"] = 3;
					}
					operation = (operation and ClipType[operation]) and ClipType[operation] or "union"
					filltype = (filltype and FillType[filltype]) and FillType[filltype] or "evenodd"
					cpp:Execute(	-- ejecutar operación (unión, intersección, diferencia o xor)
						operation,	-- Tipo de operación
						filltype,	-- Tipo de relleno para subject
						filltype	-- Tipo de relleno para clip
					)--PolyFillType: "pftEvenOdd" = 0, "pftNonZero" = 1, "pftPositive" = 2, "pftNegative" = 3
					local result = cpp.FinalSolution
					return ke.shape.clipper.toshape(result)
				end, --ke.shape.clipper.boolean("m 0 0 l 0 50 l 30 50 l 30 0 l 0 0 m 10 10 l 20 10 l 20 40 l 10 40 l 10 10 ", "m -5 20 l -5 30 l 40 30 l 40 20 l -5 20 ", "difference")
				
			},
			-------------------------------
			
			["__index"] = function(self, name)
				local specials = {
					"minx", "maxx", "miny", "maxy", "n", "width", "height", "center",
					"middle", "radius", "centroid", "seg", "pnt", "len", "isclosed"
				}
				if ke.table.inside(specials, name) then
					return ke.shape.get(self, name)
				end
				return ke.shape[name]
			end,
			
			["get"] = function(self, name)
				--most relevant information from the shape
				local minx, maxx, miny, maxy, n = math.huge, -math.huge, math.huge, -math.huge, 0
				for x, y in self.code:gmatch("(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)") do
					minx, miny = math.min(minx, x), math.min(miny, y)
					maxx, maxy = math.max(maxx, x), math.max(maxy, y)
					n = n + 1
				end
				local values = {}
				values.n = n
				values.minx, values.maxx = minx, maxx		--min and max values in "x"
				values.miny, values.maxy = miny, maxy		--min and max values in "y"
				values.width  = maxx - minx																--shape width
				values.height = maxy - miny																--shape height
				values.center = minx + values.width / 2													--center shape ("x")
				values.middle = miny + values.height / 2												--middle shape ("y")
				values.radius = ke.math.distance(values.width, values.height) / 2						--shape radius
				values.centroid = ke.shape.point.new(minx + values.width / 2, miny + values.height / 2)	--shape point center
				values.seg = name == "seg" and self:__seg() or nil										--shape segments
				values.pnt = name == "pnt" and self:points() or nil										--shape points
				values.len = name == "len" and self:length() or nil										--shape length (perimeter)
				values.isclosed = self:__isclosed()														--true or false
				return values[name]
			end, --shp = ke.shape.new(ke.shape.rectangle)
			
			["new"] = function(asscode)
				local code = (type(asscode) == "table" and asscode.code) and asscode.code or asscode
				code = type(code) == "table" and ke.shape.tocode(code) or code
				code = ke.shape.assdraw(code:gsub("c%s?", "")):gsub("nil", "m")
				local self = {code = code}
				setmetatable(self, ke.shape)
				return self
			end, --ke.shape.new(ke.shape.circle):round()
			
			["gsub"] = function(self, filter, aux, count)
				local self = ke.shape.__init(self)
				if type(filter) == "string" then
					self.code = self.code:gsub(filter, aux, count)
					return self
				end
				local i, n = ke.math.count(), self.n
				local env = ke.table.setvalues()
				local center, middle, minx = self.center, self.middle, self.minx
				local width, height, miny = self.width, self.height, self.miny
				self.code = self.code:gsub("(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)",
					function(x, y)
						local k = i()
						env.set({
							Cx = center,									--coordenada "x" del centro
							Cy = middle,									--coordenada "y" del centro
							Do = ke.math.distance(x, y),					--distancia del punto al origen
							Dc = ke.math.distance({center, middle}, {x, y}),--distancia del punto al centro
							Ao = ke.math.angle({0, 0}, {x, y}),				--ángulo del origen al punto
							Ac = ke.math.angle({center, middle}, {x, y}),	--ángulo del centro al punto
							Pn = n,											--cantidad total de puntos
							Pk = k,											--contador de los puntos
							Mx = (y - miny) / height,						--varianza respecto a "x", Mx = [0, 1]
							My = (x - minx) / width,						--varianza respecto a "y", My = [0, 1]
							Mp = (k - 1) / (n - 1)							--varianza respecto a los puntos, Mp = [0, 1]
						})
						x, y = filter(x, y, self)
						return ("%s %s"):format(ke.math.round(x, ROUND_NUM), ke.math.round(y, ROUND_NUM))
					end
				)
				env.reset()
				return self
			end, --ke.shape.new(ke.shape.rectangle):gsub(function(x, y) y = y - Cx return x, y end).code
			
			["gmatch"] = function(self, pattern)
				local self = ke.shape.__init(self)
				local result = ke.table.new()
				local special = {
					["parts"]  = "[mlb][^mlb]*",	["coors"]   = "(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)",
					["shapes"] = "m[^m]*",			["beziers"] = "b%s+[%- %.%d]*",
					["points"] = ke.shape.points,	["lines"]   = "l%s+[%- %.%d]*",
					["tracts"] = ke.shape.tract,	["numbers"] = "%-?%d[%.%d]*",
					["segs"]   = ke.shape.__seg
				}
				local cap, i = special[pattern] or pattern, 0
				if pattern == "points" or pattern == "tracts" or pattern == "segs" then
					result = ke.table.filter(special[pattern](self), function(k, v) return {v} end)
				else
					for A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P in self.code:gmatch(cap) do
						result:insert({A, B, C, D, E, F, G, H, I, J, K, L, M, N, O, P})
					end
				end
				return function()
					i = next(result, i)
					if i then
						return i, table.unpack(result[i])
					end
				end --for i, p in self:gmatch("points") do...
			end,
			
			["__call"] = function(self, tract, section)
				return type(tract) == "function" and self:filter(tract) or self:redraw(tract, section)
			end,
			
			["__ipairs"] = function(self)
				local shapes = ke.table.new(self.code:gmatch("m[^m]*"))
				local i = 0
				return function()
					i = i + 1
					if shapes[i] then
						return i, ke.shape.new(shapes[i])
					end
				end
			end,
			
			["__add"] = function(self, xy)
				--moves the shape relative to the xy plane
				local dx = type(xy) == "table" and xy[1] or xy or 0
				local dy = type(xy) == "table" and xy[2] or 0
				if type(xy) == "table" and xy.code then
					return self:__concat(xy)
				end --concat the shapes
				return self:gsub(function(x, y) return x + dx, y + dy end) --move the shape
			end, --ke.shape.new(ke.shape.rectangle) + 7
			
			["__sub"] = function(self, xy)
				--moves the shape relative to the xy plane
				local dx, dy = ke.math.getpair(xy, 0, 0)
				return self:gsub(function(x, y) return x - dx, y - dy end)
			end, --ke.shape.new(ke.shape.rectangle) - 5
			
			["__mul"] = function(self, xy)
				--scaling of the shape by a given ratio
				local rx, ry = ke.math.getpair(xy, 1)
				return self:gsub(function(x, y) return x * rx, y * ry end)
			end, --ke.shape.new(ke.shape.rectangle) * 0.25
			
			["__div"] = function(self, xy)
				--scaling of the shape by a given ratio
				local rx, ry = ke.math.getpair(xy, 1)
				return self:gsub(function(x, y) return x / rx, y / ry end)
			end, --ke.shape.new(ke.shape.rectangle) / 2
			
			["__red"] = function(self)
				--remove collinear points shape
				local self = ke.shape.__init(self)
				local P = self:points()
				local function get_reduce(P1, P2, P3)
					return ke.math.equality(P1:angle(P2), P1:angle(P3), 2)
				end
				local newpoints = {P[1]}
				for i = 2, #P - 1 do
					newpoints[#newpoints + 1] = not (P[i].t == "l" and P[i + 1].t == "l" and get_reduce(P[i - 1], P[i], P[i + 1]))
					and P[i] or nil
				end
				newpoints[#newpoints + 1] = P[#P]
				self.code = ke.shape.new(newpoints).code
				return self
			end, --ke.shape.__red("m 0 0 l 24 6 l 48 -7 l 65 16 l 50 30 l 43 12 l -12 26 ")
			
			["__seg"] = function(self)
				--obtains the individual segments of a shape
				local self = ke.shape.__init(self)
				local tracts = self:tract()
				return ke.table.new(tracts.n, function(i) return ke.shape.segment.new(tracts[i]) end)
			end, --ke.shape.new(ke.shape.circle):__seg()
			
			["__type"] = function(self)
				return "shape"
			end,
			
			["__copy"] = function(self)
				return ke.table.copy(self)
			end,
			
			["__init"] = function(self, default)
				--transforms the shape into an object of the class ke.shape
				local newself = type(self) == "function" and self() or self or default
				newself = type(newself) == "string" and ke.shape.new(newself) or newself
				return ke.shape.__copy(newself)
			end,
			
			["__concat"] = function(self, other)
				--concatenate the code of two shapes
				local self = ke.shape.__init(self)
				other = type(other) == "function" and other() or other
				local toconcat = other
				if type(other) == "table" and ke.table.type(other) == "shape" then
					toconcat = other.code
				end
				self.code = self.code .. toconcat
				return self
			end, --ke.shape.new(ke.shape.circle) .. ke.shape.pixel
			
			["__isclosed"] = function(self)
				--returns false or true if the shape is closed
				local self = ke.shape.__init(self)
				for i, s in ipairs(self) do
					local pnt = s:points()
					if pnt[1] ~= pnt[pnt.n] then
						return false
					end
				end
				return true
			end,
			
			["__closed"] = function(self)
				--converts the shape into a closed one, if it is not already.
				local self = ke.shape.__init(self)
				local newcode, addfirst = "", ""
				for i, s in ipairs(self) do
					local first = s.code:match("m (%-?%d[%.%d]* %-?%d[%.%d]* )")
					local last = s.code:match("(%-?%d[%.%d]* %-?%d[%.%d]* )$")
					addfirst = first ~= last and first or ""
					newcode = newcode .. s.code .. addfirst
				end
				self.code = newcode
				return self
			end, --ke.shape.new("m 0 0 l 0 20 l 20 20 l 20 0 m 30 20 l 30 0 l 50 0 l 50 20 "):__closed().code
			
			["__unclosed"] = function(self)
				--converts the shape into a unclosed one, if it is not already.
				local self = ke.shape.__init(self)
				local newcode = ""
				for i, s in ipairs(self) do
					local first = s.code:match("m (%-?%d[%.%d]* %-?%d[%.%d]* )")
					local last = s.code:match("(%-?%d[%.%d]* %-?%d[%.%d]* )$")
					if first == last then
						s.code = s.code:gsub("%-?%d[%.%d]* %-?%d[%.%d]* $", ""):gsub("[lm] $", "")
					end
					newcode = newcode .. s.code
				end
				self.code = newcode
				return self
			end, --ke.shape.new(ke.shape.rectangle):__unclosed()
			
			["__inv"] = function(self)
				--reverses the code of the shape, without modifying its form
				local self = ke.shape.__init(self)
				local shapes = ke.table.new()
				for i, s in ipairs(self) do
					local segs = ke.shape.tract(s.code)("inverse")
					for k, seg in ipairs(segs) do
						local aux = ke.table.new(seg:gmatch("%-?%d[%.%d]*%s+%-?%d[%.%d]*"))("inverse")
						local letter = seg:match("[mbl]")
						aux:insert(letter, 2)
						segs[k] = table.concat(aux, " ")
						segs[k] = k > 1 and segs[k]:match("[mlb][^mlb]*") or segs[k]
					end
					shapes[i] = "m " .. table.concat(segs, " "):sub(1, -2)
				end
				self.code = table.concat(shapes("inverse"), " ")
				return self
			end, --ke.shape.new(ke.shape.circle):__inv()
			
			["__area"] = function(self)
				--if the area is negative, the shape is drawn unclockwise
				--if area == 0, then either the points are collinear or the edges intersect
				local area = 0
				local self = ke.shape.__init(self)
				for _, s in ipairs(self) do
					local sum1, sum2, pnt, n = 0, 0, s:points(), s.n
					for i = 1, n do
						sum1 = sum1 + (pnt[i].x * pnt[i % n + 1].y)
						sum2 = sum2 + (pnt[i].y * pnt[i % n + 1].x)
					end
					area = area + (sum1 - sum2) / 2
				end
				return ke.math.round(area, ROUND_NUM)
			end, --ke.shape.new(ke.shape.rectangle):__area()
			
			["isclockwise"] = function(self)
				--returns false or true if the shape is drawn clockwise
				return self:__area() > 0
			end,
			
			["clockwise"] = function(self)
				--redraws a shape so that its path is clockwise
				local self = ke.shape.__init(self)
				local newcode = self:__area() <= 0 and self:__inv().code or self.code
				self.code = newcode
				return self
			end, --ke.shape.new("m 0 0 l 0 20 l 20 20 l 20 0 "):clockwise()
			
			["unclockwise"] = function(self)
				--redraws a shape so that its path is unclockwise
				local self = ke.shape.__init(self)
				return self:__area() > 0 and self:__inv() or self
			end, --ke.shape.new("m 0 0 l 0 20 l 20 20 l 20 0 "):unclockwise()
			
			["__tostring"] = function(self)
				return self.code
			end, --tostring(ke.shape.new(shape.circle))
			
			["__del"] = function(self, delete, initial)
				--removes the point(s) indicated in a shape
				local self = ke.shape.__init(self)
				local points, delete = self:__copy():points(), delete or 0
				local del1 = type(delete) == "table" and delete[1] or delete
				local del2 = type(delete) == "table" and delete[2] or del1
				del1 = del1 < 0 and #points + del1 + 1 or del1
				del2 = del2 < 0 and #points + del2 + 1 or del2
				points = ke.table.get(points, "delete", {{del1, del2}})
				points[1].t = initial and "m" or points[1].t
				self.code = ke.shape.new(points).code
				return self
			end, --ke.shape.new(ke.shape.rectangle):__del({4, 5}).code
			
			["__rep"] = function(self, n)
				--repeat the shape code
				local self = ke.shape.__init(self)
				n = type(n) == "function" and n() or n
				n = type(n) == "number" and math.ceil(math.abs(n)) or 1
				self.code = self.code:rep(n)
				return self
			end, --ke.shape.new(ke.shape.rectangle):__rep(3)
			
			assdraw = function(asscode)
				--formats the code of a shape or a rectangular clip as assDraw3
				if type(asscode) == "table" and asscode.code then
					return asscode.code
				end
				local code = asscode:match("m%s+%-?%d[%.%-%d blm]*") or asscode
				if asscode:match("%-?%d[%. %d]*,%s*%-?%d[%. %d]*,%s*%-?%d[%. %d]*,%s*%-?%d[%. %d]*") then
					local x1, y1, x2, y2 = asscode:match( "(%-?%d[%. %d]*),%s*(%-?%d[%. %d]*),%s*(%-?%d[%. %d]*),%s*(%-?%d[%. %d]*)")
					code = ("m %s %s l %s %s l %s %s l %s %s "):format(x1, y1, x1, y2, x2, y2, x2, y1)
				end
				code = code:gsub("([mbl]^*)(%s+%-?%d[%.%- %d]*)",
					function(bl, numbers)
						local k, i = ke.math.count(), bl == "b" and 6 or 2
						return bl .. numbers:gsub("%-?%d[%.%d]*",
							function(num)
								local num = ke.math.round(num, ROUND_NUM)
								return k() % i == 0 and num .. " " .. bl or num
							end
						):gsub(" +", " "):sub(1, -3)
					end
				)
				return code
			end,
			
			points = function(self, coors)
				--gets the points from the shape
				local self = ke.shape.__init(self)
				local pnt = ke.table.new()
				for t, nums in self.code:gmatch("([mbl]^*)(%s+%-?%d[%. %-%d]*)") do
					for x, y in nums:gmatch("(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)") do
						pnt:insert(ke.shape.point.new(x, y, t))
					end
				end
				return not coors and pnt or ke.shape.point.group(pnt, "coors")
			end,
			
			tocode = function(points)
				--shape code from a set of points
				if type(points) == "table" and (points.coorsx or points.coorsy) then --coors to points
					local coorsx = points.coorsx or 0
					local coorsy = points.coorsy or 0
					points = ke.table.new()
					if type(coorsx) == "table" then
						for i, x in ipairs(coorsx) do
							local y = type(coorsy) == "table" and coorsy[i] or coorsy
							points:insert(ke.shape.point.new(x, y, "l"))
						end
					elseif type(coorsy) == "table" then
						for i, y in ipairs(coorsy) do
							local x = type(coorsx) == "table" and coorsx[i] or coorsx
							points:insert(ke.shape.point.new(x, y, "l"))
						end
					end
					points[1].t = "m"
				end --ke.shape.new({coorsx = {4, -5, 1, 0, 2}})
				if ke.table.type(points[1]) == "segment" then --segments to points
					local aux = {}
					for _, s in ipairs(points) do
						for _, p in ipairs(s) do
							p.t = s.t
							table.insert(aux, p)
						end
					end
					points = aux
				end
				local code = ("%s %s %s "):format(points[1].t, points[1].x, points[1].y)
				for i = 2, #points do
					local letter = points[i].t == points[i - 1].t and "" or points[i].t
					code = code .. ("%s %s %s "):format(letter, points[i].x, points[i].y)
				end
				code = code:gsub("%s+", " ")
				return code
			end,
			
			tract = function(self)
				--gets the code of the shape segments
				local self = ke.shape.__init(self)
				local tracts, i = ke.table.new(), ke.math.count()
				for seg in self.code:gmatch("[mlb][^mlb]*") do
					local k = i()
					if k > 1 and not seg:match("m") then
						seg = tracts[k - 1]:match("%-?%d[%.%d]*%s+%-?%d[%.%d]*%s?$") .. seg
					end
					tracts:insert(seg)
				end
				return tracts
			end, --ke.shape.new(ke.shape.circle):tract()
			
			bounding = function(self)
				--min and max values in thne bounding box
				return self.minx, self.miny, self.maxx, self.maxy
			end,
			
			box = function(self)
				--bounding points: lt, lb, rb, rt
				local x0, y0, x1, y1 = self:bounding()
				local p0, p1 = ke.shape.point.new(x0, y0), ke.shape.point.new(x0, y1)
				local p2, p3 = ke.shape.point.new(x1, y1), ke.shape.point.new(x1, y0)
				return p0, p1, p2, p3
			end,
			
			round = function(self, n)
				--rounds the shape values ​​to the indicated decimal place
				local self = ke.shape.__init(self)
				self.code = self.code:gsub("%-?%d[%.%d]*", function(num) return ke.math.round(num, n or 0) end)
				return self
			end,
			
			redraw = function(self, tract, section)
				--divides the segments of the shape into segments of specified length
				local self = ke.shape.__init(self)
				tract, section = ke.math.__init(tract, 2), section or "all"
				local t = section == "line" and "l" or (section == "bezier" and "b" or section)
				local segs = self:__seg()
				local rseg = ke.table.new(segs.n, function(i) return (segs[i].t == t or t == "all") and segs[i]:split(tract) or segs[i] end)
				self.code = ke.shape.new(rseg).code
				return self
			end, --ke.shape.new("m 10 0 b 0 0 0 10 10 10 l 30 10 b 40 10 40 0 30 0 l 10 0 "):redraw(4, "line"):round()
			
			length = function(self)
				--total shape perimeter
				local self = ke.shape.__init(self)
				local segs = self:__seg()
				local length = segs:iter(function(i, v, s) return s + v:length() end, 0)
				return ke.math.round(length, ROUND_NUM)
			end, --ke.shape.length(ke.shape.circle)
			
			rand = function(self, configs)
				--randomly creates or modifies the points of a shape
				--configs = {rx = val or table, ry = val or table, step = val}
				--configs = {dx = val or table, dy = val or table, n = integer_number}
				local rx, ry, st, split, section = 24, 24, 1
				local dx, dy, n, config_filter = 100, 100, 12
				if configs and type(configs) == "table" then
					dx, dy, n = configs.dx or dx, configs.dy or dy, configs.n or n
					rx, ry, st = configs.rx or rx, configs.ry or ry, configs.step or st
					split, section = configs.split or split, configs.section or section
					config_filter = configs.filter or config_filter
				end
				local default = ke.shape.point.toshape(ke.shape.point.toconvex(ke.shape.point.rand(nil, {n = n, dx = dx, dy = dy})))
				self = ke.shape.__init(self, default)
				self = split and self:redraw(split, section) or self
				local filter = function(x, y)
					local prx = type(rx) == "table" and ke.math.rand(rx[1], rx[2], st) or ke.math.rand(0, rx, st)
					local pry = type(ry) == "table" and ke.math.rand(ry[1], ry[2], st) or ke.math.rand(0, ry, st)
					return x + prx, y + pry
				end
				return self:gsub(config_filter or filter)
			end, --ke.shape.rand(ke.shape.rectangle, {rx = 5, ry = 5, split = 4})
			
			displace = function(self, move)
				--two-dimensional shape displacement
				--> move = {x = val, y = val, point = num, mode = str}
				local self = ke.shape.__init(self)
				move = type(move) == "number" and {x = move} or move or {x = 0, y = 0}
				local dx, dy = ke.math.__init(move.x, 0), ke.math.__init(move.y, 0)
				local disp = {dx, dy}
				if move.mode then
					local pnt, n = self:points(), self.n
					local xmoves = {
						["origin"]	= {dx - self.minx, dy - self.miny},
						["center"]	= {dx - self.minx - 0.5 * self.width, dy - self.miny - 0.5 * self.height},
						["polar"]	= {ke.math.polar(dx, dy)},
						["first"]	= {dx - pnt[1].x, dy - pnt[1].y},
						["last"]	= {dx - pnt[n].x, dy - pnt[n].y},
						["point"]	= {dx - pnt[move.point or 1].x, dy - pnt[move.point or 1].y},
					}
					disp = xmoves[move.mode] or disp
				end --ke.shape.displace(ke.shape.circle, {x = 20, y = 20, mode = "point"})
				return self + disp
			end, --ke.shape.displace(ke.shape.circle, {x = 20, y = 10})
			
			ratio = function(self, xratio, yratio, mode)
				--modifies the size of the shape with respect to a proportion (ratio)
				local self = ke.shape.__init(self)
				xratio, yratio = ke.math.__init(xratio), ke.math.__init(yratio)
				mode = type(mode) == "function" and mode() or mode
				local x0, y0, x1, y1 = self:bounding()
				local wx, hy = self.width, self.height
				local pnt, n, rx = self:points(), self.n, xratio or 1
				if type(xratio) == "table" then
					rx = (xratio[1] or wx) / wx
					if #xratio == 2 then --rx depends on the distance between two points or a point and the origin
						xratio[1] = not xratio[1] and {pnt[1], pnt[n]} or xratio[1]
						rx = xratio[2] / ke.math.distance(xratio[1])
						rx = ke.math.distance(xratio[1]) == 0 and xratio[2] / wx or rx
					end
				end
				local ry, disp = yratio or rx, {0, 0}
				if yratio and type(yratio) == "table" then
					ry = yratio[1] / hy
					rx = xratio == nil and ry or rx
				end
				if mode then --move the shape to the notable positions of the original shape
					local xpos = {x0 * (1 - rx), self.center * (1 - rx), x1 * (1 - rx), first = pnt[1].x * (1 - rx), last = pnt[n].x * (1 - rx)}
					local ypos = {y1 * (1 - ry), self.middle * (1 - ry), y0 * (1 - ry), first = pnt[1].y * (1 - rx), last = pnt[n].y * (1 - rx)}
					disp = {
						type(mode) == "string" and xpos[mode] or xpos[(mode - 1) % 3 + 1],
						type(mode) == "string" and ypos[mode] or ypos[math.ceil(mode / 3)]
					}
				end
				self = self:gsub(function(x, y) return x * rx, y * ry end)
				return self + disp
			end, --ke.shape.ratio(ke.shape.rectangle, 0.2, nil, 8)
			
			size = function(self, xsize, ysize, mode)
				--modifies the size of the shape with respect to certain values
				--if xsize is an array, xsize[1] will be added to the width  of the shape
				--if ysize is an array, ysize[1] will be added to the height of the shape
				local self = ke.shape.__init(self)
				xsize = ke.math.__init(xsize, self.width)
				ysize, mode = ke.math.__init(ysize, xsize), ke.math.__init(mode)
				local xrat = type(xsize) == "table" and self.width  + xsize[1] or xsize
				local yrat = type(ysize) == "table" and self.height + ysize[1] or ysize
				xrat = yrat == 0 and {xrat} or (xrat ~= 0 and (self.width  > 0 and xrat / self.width  or 1)) or nil
				yrat = xrat == 0 and {yrat} or (yrat ~= 0 and (self.height > 0 and yrat / self.height or 1)) or nil
				--x = 0: "x" is proportionally modified depending on how "y" is modified
				--y = 0: "y" is proportionally modified depending on how "x" is modified
				return self:ratio(xrat, yrat, mode) --ke.shape.size(ke.shape.rectangle, 120, 0)
			end, --ke.shape.size(ke.shape.rectangle, 120, 45)
			
			glue = function(self, other, mode, split)
				--causes one shape to adopt the characteristic form of another
				local self = ke.shape.__init(self)
				split = type(split) == "function" and split() or split or 2
				mode = mode or 1
				local width = self.width
				self = self:redraw(split) --shape
				other  = ke.shape.new(other:match("m%s+%-?%d[%.%-%d lb]*")):redraw(3)
				local ratio  = ke.math.round(width / other:length(), ROUND_NUM)
				local filter = type(mode) == "function" and mode or nil
				filter = other:length() < width and function(x, y) return x, y end			--default
				or (mode == 1 and function(x, y) return (1 - ratio) / 2 + ratio * x, y end)	--centrado
				or (mode == 2 and function(x, y) return ratio * x, y end)					--de inicio a fin
				or (mode == 3 and function(x, y) return 1 - ratio + ratio * x, y end)		--de fin a inicio
				or (mode == 4 and function(x, y) return x, y end) or filter					--justificado a lo largo
				local segments, length, n, l, last = {}, 0, 0
				other = other:gsub(
					function(x, y)
						if last then
							l = {last[1], last[2], x - last[1], y - last[2], ke.math.distance(x - last[1], y - last[2])}
							if l[5] > 0 then
								n = n + 1
								segments[n] = l
								length = length + l[5]
							end
						end
						last = {x, y}
						return x, y
					end
				)
				if n > 0 then
					local curve = 0
					for _, l in ipairs(segments) do
						l[6] = curve / length
						curve = curve + l[5]
						l[7] = curve / length
					end
					local x0, y0, x1, y1 = self:bounding()
					if x0 and x1 > x0 then
						local ortho = function(x1, y1, z1, x2, y2, z2)
							return y1 * z2 - z1 * y2, z1 * x2 - x1 * z2, x1 * y2 - y1 * x2
						end
						local stretch = function(x, y, length)
							local  curve = (x * x + y * y) ^ 0.5
							return curve == 0 and 0 or x * length / curve, curve == 0 and 0 or y * length / curve
						end
						local pos, ox, oy, px, py, dx, dy
						return self:gsub(
							function(x, y)
								px, py = (x - x0) / width, y - y1
								dx, dy = filter(px, py)
								px, py = math.max(0, math.min(dx, 1)), dy
								for i = 1, n do
									l = segments[i]
									if px >= l[6] and px <= l[7] then
										pos = (px - l[6]) / (l[7] - l[6])
										ox, oy = ortho(l[3], l[4], 0, 0, 0, -1)
										ox, oy = stretch(ox, oy, py)
										return l[1] + pos * l[3] + ox, l[2] + pos * l[4] + oy
									end
								end
							end
						)
					end
				end
			end, --ke.shape.glue(ke.shape.size(ke.shape.rectangle, 240, 20), ke.shape.circle)
			
			rotate = function(self, angle, org)
				--rotate the shape about the "z" axis with a predetermined point of origin
				local self = ke.shape.__init(self)
				org, angle = ke.math.__init(org, {x = 0, y = 0}), ke.math.__init(angle, 0)
				local pnt = self.pnt
				local cx, cy, ang = 0, 0, angle
				org = org == "center" and ke.shape.point.new(self.center, self.middle) or org
				if type(org) == "number" then
					local p = pnt[math.ceil(org)] or {x = 0, y = 0}
					org = {x = p.x, y = p.y}
				end --ke.shape.rotate(ke.shape.rectangle, -45, 2):round()
				cx, cy = org.x, org.y
				if type(angle) == "table" then
					--ang depende del ángulo entre dos puntos o un punto y el origen
					angle[1] = not angle[1] and {pnt[1], pnt[pnt.n]} or angle[1]
					ang = (angle[2] or 0) - ke.math.angle(angle[1])
				end --ke.shape.rotate(ke.shape.rectangle, -45, "center")
				local filter_rotate = function(x, y)
					local new_ang = ke.math.angle({cx, cy}, {x, y})
					local new_rad = ke.math.distance({cx, cy}, {x, y})
					local angle = type(ang) == "function" and ang(x, y) or ang
					x = cx + ke.math.polar(new_ang + angle, new_rad, "x")
					y = cy + ke.math.polar(new_ang + angle, new_rad, "y")
					return x, y --ke.shape.rotate(ke.shape.redraw(ke.shape.rectangle, 5), function(x, y) return x * y end)
				end --ke.shape.rotate(ke.shape.redraw(ke.shape.rectangle, 5), function(x, y) return tag.ipol(Mp, 0, 60) end)
				return self:gsub(filter_rotate) --ke.shape.rotate(ke.shape.rectangle, -45)
			end,
			
			reflect = function(self, axis, relative)
				--makes a reflection of the shape with respect to any of the 2 axes, or to the line y = x
				--It can also be reflect about the lines x = relative or y = relative
				local self = ke.shape.__init(self)
				axis, relative = ke.math.__init(axis), ke.math.__init(relative, 0)
				relative, axis = not axis and self.maxx or relative, axis or "y"
				local filter_reflect = function(x, y)
					x = axis == "x" and x or ((axis == "y" or axis == nil) and relative - x) or -relative - x
					y = axis == "x" and relative - y or ((axis == "y" or axis == nil) and y) or -relative - y
					return x, y
				end
				return self:gsub(filter_reflect)
			end, --ke.shape.reflect("m 0 0 l 0 50 l 30 50 l 30 30 ", "y")
			
			oblique = function(self, pixels, t)
				--shape modifies respect to its bounding box
				local self = ke.shape.__init(self)
				local cx, cy = 0.4 * self.width, 0.4 * self.height
				local pxs, t = pixels or cx, t or 1
				local fxbox = {{0, 0}, {0, 0}, {0, 0}, {0, 0}}
				fxbox = type(pxs) == "number" and {{pxs, 0}, {0, 0}, {0, 0}, {pxs, 0}} or fxbox
				if type(pxs) == "table" and (pxs.x or pxs.y) then
					local cx, cy = pxs.x or {0, 0, 0, 0}, pxs.y or {0, 0, 0, 0}
					fxbox = {{cx[1] or 0, cy[1] or 0}, {cx[2] or 0, cy[2] or 0}, {cx[3] or 0, cy[3] or 0}, {cx[4] or 0, cy[4] or 0}}
				elseif type(pxs) == "string" and pxs == "random" then
					fxbox = ke.table.new(4, function(i) return {ke.math.rand(-cx, cx), ke.math.rand(-cy, cy)} end)
				end
				local P0, P1, P2, P3 = self:box()
				P0, P1, P2, P3 = P0 + fxbox[1], P1 + fxbox[2], P2 + fxbox[3], P3 + fxbox[4]
				local oblique_filter = function(x, y)
					local top, bottom = P0:ipol(My, {other = P3}), P1:ipol(My, {other = P2})
					local newp = top:ipol(Mx, {other = bottom})
					x, y = x + (newp.x - x) * t, y + (newp.y - y) * t
					return x, y
				end
				return self:gsub(oblique_filter)
			end, --ke.shape.oblique("m 12 8 l 12 25 l 0 25 l 0 34 l 49 34 l 49 17 l 37 17 l 37 0 l 30 0 l 30 20 l 22 20 l 22 8 l 12 8 ", 20)
			
			roundout = function(self, radius, mode)
				--rounds the shape corners
				local self = ke.shape.__init(self)
				local get_t = function(p0, p1, p2, radius)
					local d1, d2 = p0:distance(p1), p1:distance(p2)
					local dmin = math.min(d1, d2) == 0 and math.max(d1, d2) or math.min(d1, d2)
					radius = radius > 0.4 * dmin and 0.4 * dmin or radius
					return radius / d1, radius / d2
				end
				local negative = radius and radius < 0
				local result = ke.table.new()
				radius = math.abs(radius or 12)
				mode = mode or "round" --or "bevel"
				for _, s in ipairs(self) do
					local pnt, n = s.pnt, s.n
					local closed = s:__isclosed()
					if closed then
						local t0, t1 = get_t(pnt[n - 1], pnt[1], pnt[2], radius)
						result:insert(pnt[1]:ipol(t1, {other = pnt[2]}))
					else
						result:insert(pnt[1])
					end
					for i, p in ipairs(pnt) do
						if p.t == "l" then
							if i > 1 and i <= n - (closed and 0 or 1) then
								local pnext = i == n and pnt[2] or pnt[i + 1]
								local t0, t1 = get_t(pnt[i - 1], p, pnext, radius)
								if mode == "bevel" then
									local p1, p2 = p:ipol(t0, {other = pnt[i - 1]}), p:ipol(t1, {other = pnext})
									result:insert({p1, p2}, nil, true)
								else --mode = "round"
									local p1, p2 = p:ipol(t0, {other = pnt[i - 1]}), p:ipol(0.42 * t0, {other = pnt[i - 1]})
									local p3, p4 = p:ipol(0.42 * t1, {other = pnext}), p:ipol(t1, {other = pnext})
									if negative then
										p2, p3 = p2:reflect(p1, p4), p3:reflect(p1, p4)
									end
									p2.t, p3.t, p4.t = "b", "b", "b"
									result:insert({p1, p2, p3, p4}, nil, true)
								end
							end
						elseif p.t ~= "m" then
							result:insert(p)
						end
					end
					if not closed then
						result:insert(pnt[n])
					end
				end
				self.code = ke.shape.new(result).code
				return self
			end, --ke.shape.roundout(ke.shape.rectangle, 20)
			
			filter = function(self, split, ...)
				--applies one or more functions to the points of the shape
				self = ke.shape.__init(self)
				self = (split and split > 0) and self:redraw(split) or self
				local filters = (... and type(...) == "table") and ... or {...}
				filters[1] = #filters == 0 and function(x, y) return x, y end or filters[1]
				for i = 1, #filters do
					if type(filters[i]) == "table" or type(filters[i]) == "string" then
						local shp = type(filters[i]) == "table" and filters[i][1] or filters[i]
						local mode  = type(filters[i]) == "table" and filters[i][2] or nil
						self = self:glue(shp, mode)
					else
						self = self:gsub(filters[i])
					end
				end --ke.shape.filter(ke.shape.rectangle, 4, function(x, y) x = x + 8 * math.sin(Mx * 4 * math.pi) return x, y end)
				return self:__red()
			end, --ke.shape.filter(ke.shape.rectangle, 4, function(x, y) x = x + ke.math.rand(5) y = y + ke.math.rand(5) return x, y end)
			
			filtergroup = function(self, filter)
				--applies one or more functions to the points of the individual shapes of a shape
				local self = ke.shape.__init(self)
				if type(self) == "table" and not self.code then
					return ke.table.recurse(ke.shape.filtergroup, self, self)
				end
				local n, code = ke.string.count(self.code, "m"), ""
				for i, s in ipairs(self) do
					code = code .. filter(i, n, s, self).code
				end
				self.code = code
				return self
			end, --ke.shape.new("m 50 0 l 50 20 l 70 20 l 70 0 "):__rep(12):filtergroup(function(i, n, s, self) return s:rotate(30 * i, {x = 0, y = self.middle}) end)
			
			array = function(self, configs)
				--generates multiple arrays of one or more shapes entered
				local self, result = ke.shape.__init(self), ""
				local aux = not self.code and ke.table.new(#self, function(i) return ke.shape.new(self[i]) end) or nil
				shapes = aux or {self}
				local dx, dy, loop, radius, mode, n, alternated, guide, j, shp = 0, 0, 1, 0, "array", #shapes, false, ke.shape.circle
				if type(configs) == "table" then
					dx, dy = configs.dx or dx, configs.dy or dy
					alternated = configs.alternated or alternated
					loop, mode = configs.loop or loop, configs.mode or mode
					guide, radius = configs.guide or guide, configs.radius or radius
				end
				if mode == "random" then
					local Rc = function(A, B) return ke.math.rand(A, B, 0.01) end
					local Rs = function(A, B) return ke.math.rand(A, B, 0.01, true) end
					local R1A, R1B, R1C, R2A, R2B, R2C, R6A = Rc(10, 30), Rc(10, 30), Rc(10, 30), Rs(30),  Rs(30), Rs(30), Rc(0, 20)
					local R3A, R3B, R4A, R4B, R5A, R5B, R5C = Rc(25, 45), Rc(25, 45), Rc(20, 40), Rc(20, 40), Rs(40), Rs(40), Rs(40)
					local shp0 = {
						[1] = ("m 0 0 l %s %s l %s %s l %s %s l %s %s l 50 0 "):format(R1A, R2A, R3A, R5A, R6A, R2B, R4A, R5B),
						[2] = ("m 0 0 l %s %s l %s %s b %s %s %s %s %s %s l 50 0 "):format(R1A, R2A, R3A, R5A, R6A, R2B, R3B, R5B, R4A, R5C),
						[3] = ("m 0 0 l %s %s b %s %s %s %s %s %s l %s %s l 50 0 "):format(R1A, R2A, R3A, R5A, R6A, R2B, R3B, R5B, R4A, R5C),
						[4] = ("m 0 0 b %s %s %s %s %s %s l %s %s b %s %s %s %s 50 0 "):format(R1A, R2A, R3A, R5A, R6A, R2B, R4A, R5B, R1B, R2C, R4B, R5C),
						[5] = ("m 0 0 b %s %s %s %s %s %s b %s %s %s %s %s %s l 50 0 "):format(R1A, R2A, R3A, R5A, R6A, R2B, R4A, R5B, R1B, R2C, R4B, R5C),
						[6] = ("m 0 0 b %s %s %s %s %s %s l %s %s b %s %s %s %s 50 0 "):format(R1A, R2A, R3A, R5A, R6A, R2B, R4A, R5B, R1B, R2C, R4B, R5C, R1C, Rs(30)),
						[7] = ("m 0 0 l %s 0 b %s %s %s %s %s %s l %s %s b %s %s %s %s 50 0 "):format(R4A, R3A, R5A, R6A, R2A, R4B, R5B, R1B, R2B, Rc(20, 40), R5C, R1C, R2C),
						[8] = ("m 0 0 b %s %s %s %s %s %s l %s %s b %s %s %s %s %s %s l 50 0 "):format(R1A, R2A, R3A, R5A, R6A, R2B, R4A, R5B, R1B, R2C, R4B, R5C, R1C, Rs(30)),
					}
					local shp1 = ke.shape.new(ke.math.rand(shp0))
					local shp2 = shp1:__inv():reflect("x").code:gsub("m 50 0 ", "")
					shapes, mode, n = {ke.shape.ratio(shp1 .. shp2, {ke.math.rand(36, 50, 0.01)})}, "radial", 1
				end
				local xmax = ke.table.get(ke.table.new(#shapes, function(i) return shapes[i].width end), "max")
				local ymax = ke.table.get(ke.table.new(#shapes, function(i) return shapes[i].height end), "max")
				local loopx = type(loop) == "table" and loop.x or loop
				local loopy = type(loop) == "table" and loop.y or 1
				if mode == "shape" then
					local confi = ke.shape.parameter(guide, nil, loopx)
					for i = 1, loopx do
						j = (i - 1) % n + 1
						shp = (alternated and (j - 1) % 2 == 1) and shapes[j]:__inv() or shapes[j]
						result = result .. shp:displace({mode = "center"}):rotate(confi[i][2]):displace({x = confi[i][1].x, y = confi[i][1].y})
					end --ke.shape.array(ke.shape.size(ke.shape.rectangle, 10, 20), {loop = 18, mode = "shape", guide = ke.shape.circle, alternated = true}):round()
				elseif mode == "radial" then
					for i = 1, loopy do
						for k = 1, loopx do
							j = (i + k - 2) % n + 1
							shp = (alternated and (i + k) % 2 == 1) and shapes[j]:__inv() or shapes[j]
							result = result .. shp:displace({mode = "center",
								x = 0.5 * xmax + (i - 1) * (xmax + dx) + radius
							}):rotate((k - 1) * 360 / loopx)
						end
					end --ke.shape.array({"m 0 0 l 0 12 12 12 12 0 ", "m 0 0 l 0 20 l 10 30 l 20 20 l 20 0 "}, {loop = {x = 8, y = 3}, mode = "radial", radius = 20, dx = 5}):round()
				else --"array"
					for i = 1, loopy do
						for k = 1, loopx do
							j = (i + k - 2) % n + 1
							shp = (alternated and (i + k) % 2 == 1) and shapes[j]:__inv() or shapes[j]
							result = result .. shp:displace({mode = "center",
								x = 0.5 * xmax + (k - 1) * (xmax + dx), y = 0.5 * ymax + (i - 1) * (ymax + dy)
							})
						end
					end --ke.shape.array("m 0 0 l 0 12 12 12 12 0 0 0 ", {loop = {x = 5, y = 3}, dx = 5, dy = 5})
				end
				return result:displace({mode = "origin"})
			end,
			
			multi1 = function(size, px)
				--returns concentric square shapes
				size, px = ke.math.__init(size, 100), ke.math.__init(px, 4)
				local shpw, pxi, px1, i = 0, 0, 0, 1
				px = type(px) == "number" and {px} or px
				px1 = type(px) == "table" and px[1] or (type(px) == "function" and px() or px1)
				shpw = px1
				local shp = ("m 0 0 l 0 %s l %s %s l %s 0 l 0 0 "):format(px1, px1, px1, px1)
				while 2 * shpw < size do
					pxi = type(px) == "table" and px[i % #px + 1] or (type(px) == "function" and px(i) or pxi)
					shpw = shpw + (type(pxi) == "table" and pxi[1] or pxi)
					if type(pxi) == "number" then
						shp = shp .. ("m %s %s l %s %s l %s %s l %s %s l %s %s l %s %s l %s %s l %s %s l %s %s l %s %s "):format(
							-shpw + px1, -shpw + px1, -shpw + px1, shpw, shpw, shpw, shpw, -shpw + px1, -shpw + px1,
							-shpw + px1, -shpw + px1 + pxi, -shpw + px1 + pxi, shpw - pxi, -shpw + px1 + pxi, shpw - pxi,
							shpw - pxi, -shpw + px1 + pxi, shpw - pxi, -shpw + px1 + pxi, -shpw + px1 + pxi
						)
					end
					i = i + 1
				end
				return ke.shape.new(shp):displace({mode = "origin"})
			end, --ke.shape.multi1(100, {8, {2}, 4, {3}})
			
			multi2 = function(width, height, pixel)
				--create diagonal shapes inside a rectangle with given measurements
				width, height = ke.math.__init(width, 70), ke.math.__init(height, 50)
				pixel = ke.math.__init(pixel, 6)
				pixel = type(pixel) == "number" and {pixel} or pixel
				local dimension = height > width and {x = height, y = width} or {x = width, y = height}
				local i, pxi = 1, 0
				local shp = ("m 0 0 l 0 %s l %s 0 l 0 0 l 0 0 "):format(pixel[1], pixel[1])
				local dy = pixel[1]
				while dy < dimension.y do
					pxi = type(pixel) == "table" and pixel[i % #pixel + 1] or 0
					dy = dy + ((type(pxi) == "table") and pxi[1] or pxi)
					if type(pxi) == "number" then
						shp = shp .. ("m 0 %s l 0 %s l %s 0 l %s 0 l 0 %s "):format(dy - pxi, dy, dy, dy - pxi, dy - pxi)
					end
					i = i + 1
				end
				local dx, shp_y = dy, dy
				while dx < dimension.x do
					pxi = type(pixel) == "table" and pixel[i % #pixel + 1] or 0
					dx = dx + ((type(pxi) == "table") and pxi[1] or pxi)
					if type(pxi) == "number" then
						shp = shp .. ("m %s %s l %s %s l %s 0 l %s 0 l %s %s "):format(
							dx - shp_y - pxi, shp_y, dx - shp_y, shp_y, dx, dx - pxi, dx - shp_y - pxi, shp_y
						)
					end
					i = i + 1
				end
				local shp_x = 0
				while shp_x < shp_y do
					pxi = type(pixel) == "table" and pixel[i % #pixel + 1] or 0
					shp_x = shp_x + ((type(pxi) == "table") and pxi[1] or pxi)
					if type(pxi) == "number" and shp_x <= shp_y then
						shp = shp .. ("m %s %s l %s %s l %s %s l %s %s l %s %s "):format(
							dx - shp_y + shp_x - pxi, shp_y, dx - shp_y + shp_x, shp_y, dx,
							shp_x, dx, shp_x - pxi, dx - shp_y + shp_x - pxi, shp_y
						)
					end
					i = i + 1
				end
				shp = ke.shape.new(shp)
				shp = height > width and shp:rotate(-90):reflect() or shp
				return shp
			end, --ke.shape.multi2(36, 94, {10, {2}, 5, {3}})
			
			multi3 = function(self, size, bord)
				--if it is not put "self", it returns concentric circles, or concentric shapes of the one that has been entered
				size, bord = ke.math.__init(size, 100), ke.math.__init(bord, 4)
				local self = ke.shape.__init(self, ke.shape.circle)
				bord = type(bord) == "number" and {bord} or bord
				local i, shp1, shp2, scon = 1
				local smax, bi = bord[1], 0
				size = (size == "default" or size == nil) and 100 or size
				local shp = self:size(bord[1]):displace({mode = "center"})
				while smax <= size do
					bi = type(bord) == "table" and bord[i % #bord + 1] or bi
					smax = smax + 2 * ((type(bi) == "table") and bi[1] or bi)
					if type(bi) == "number" then
						shp1 = ke.shape.size(self.code, smax):displace({mode = "center"})
						shp2 = ke.shape.size(self.code, smax - 2 * bi):__inv():displace({mode = "center"})
						scon = shp1.code .. shp2.code:gsub("m", "l", 1)
						shp = shp .. scon
					end
					i = i + 1
				end
				return shp:displace({mode = "origin"})
			end, --ke.shape.multi3(ke.shape.rectangle, 100, {8, {5}})
			
			multi4 = function(size, loop1, loop2, n)
				--returns a regular polygon of loop1 sides, with an array of loop2. n is the number of arrangements taken into account
				size, n = ke.math.__init(size, 64), ke.math.__init(n, 25)
				loop1, loop2 = ke.math.__init(loop1, 6), ke.math.__init(loop2, 1)
				loop1, loop2 = loop1 < 3 and 3 or loop1, loop2 <= 0 and 1 or loop2
				local sizer = 2 * math.ceil(size / 2)
				local px = ke.math.round(0.5 * sizer / loop2)
				local function multi40(size40, loop40, px40)
					local size40 = 2 * math.ceil(size40 / 2)
					px40 = px40 >= size40 / 2 and size40 / 2 or px40
					local angle, shapes = 360 / loop40, {}
					for i = 1, ke.math.round(360 / angle) do
						shapes[#shapes + 1] = ("m %s %s l %s %s l %s %s l %s %s "):format(
							ke.math.polar(angle * (i - 0), size40 / 2 - px40, "x"), ke.math.polar(angle * (i - 0), size40 / 2 - px40, "y"),
							ke.math.polar(angle * (i - 0), size40 / 2, "x"), ke.math.polar(angle * (i - 0), size40 / 2, "y"),
							ke.math.polar(angle * (i - 1), size40 / 2, "x"), ke.math.polar(angle * (i - 1), size40 / 2, "y"),
							ke.math.polar(angle * (i - 1), size40 / 2 - px40, "x"), ke.math.polar(angle * (i - 1), size40 / 2 - px40, "y")
						)
					end
					return table.concat(shapes)
				end
				local pn, shp, i = sizer / 2, "", 0
				while pn > 0 and i < n do
					shp = shp .. multi40(pn * 2, loop1, px)
					pn = pn - px
					i = i + 1
				end
				shp = ke.shape.new(shp):displace({mode = "origin"})
				return loop1 % 2 == 1 and shp:rotate(((-1) ^ ((loop1 - 1) / 2)) * 90 / loop1):displace({mode = "origin"}) or shp
			end, --ke.shape.multi4(100, 6, 4, 3)
			
			multi5 = function(self, width, height, dxy)
				--returns a rectangular array of the entered shapes
				local shapes = ke.shape.__init(self, {"m 0 0 l 0 8 8 8 8 0 "})
				local aux = not shapes.code and ke.table.new(#shapes, function(i) return ke.shape.new(shapes[i]) end) or nil
				shapes, dxy = aux or {shapes}, ke.math.__init(dxy, {0, 0})
				width, height = ke.math.__init(width, 60), ke.math.__init(height, 50)
				local shp, shpt = {}, ke.table.new(#shapes, {})
				local widths  = ke.table.new(#shapes, function(i) return shapes[i].width end)
				local heights = ke.table.new(#shapes, function(i) return shapes[i].height end)
				local wmax, hmax = widths("max"), heights("max")
				for i = 1, #shapes do
					for k = 1, #shapes do
						shpt[i][k] = shapes[(k - i) % #shapes + 1]:displace({mode = "center"}):displace({x = (k - 1) * wmax, y = (i - #shapes) * hmax}).code
					end
					shpt[i] = table.concat(shpt[i])
				end --ke.shape.multi5({"m 0 0 l 0 10 l 10 10 l 10 0 ", "m 0 10 l 10 10 l 5 0 "})
				shp = ke.shape.new(table.concat(shpt)):displace({mode = "origin"})
				local dis_xy = type(dxy) == "number" and {dxy, 0} or dxy
				local length_H, length_V = math.ceil(width / (shp.width + dis_xy[1])), math.ceil(height / (shp.height + dis_xy[2]))
				return shp:array({loop = {x = length_H, y = length_V}, dx = dis_xy[1], dy = dis_xy[2]})
			end, --ke.shape.multi5()
			
			multi6 = function(size, bord, length)
				--returns the rectangle perimeter made up of individual rectangles
				size, bord = ke.math.__init(size, 104), ke.math.__init(bord, 4)
				local xsize = type(size) == "table" and size[1] or size
				local ysize = type(size) == "table" and size[2] or size
				local spacex = type(bord) == "table" and bord[2] or 0
				length, bord = ke.math.__init(length, 20), type(bord) == "table" and bord[1] or bord
				local xloop = math.ceil((xsize - bord) / (length + spacex))
				local yloop = math.ceil((ysize - bord) / (length + spacex))
				xsize, ysize = xloop * (length + spacex) + bord - spacex, yloop * (length + spacex) + bord - spacex
				local rectangle = ke.shape.new("m 0 100 l 100 100 l 100 0 l 0 0 "):size(length, bord)
				local shp_H = rectangle:array({loop = {x = xloop}, dx = spacex})
				local shp_V = yloop == xloop and shp_H or rectangle:array({loop = {x = yloop}, dx = spacex})
				local parts = {
					[1] = shp_H.code,
					[2] = shp_V:rotate(-90):displace({point = 4, x = xsize + spacex, y = 0, mode = "point"}).code,
					[3] = shp_H:rotate(180):displace({point = 4, x = xsize + spacex, y = ysize + spacex, mode = "point"}).code,
					[4] = shp_V:rotate( 90):displace({point = 4, x = 0, y = ysize + spacex, mode = "point"}).code
				} --ke.shape.multi6({120, 30}, {4, 5}, 8)
				return ke.shape.new(table.concat(parts))
			end, --ke.shape.multi6()
			
			multi7 = function(part, radius)
				--returns a perimeter circle made up of individual segments
				radius, part = ke.math.__init(radius, 50), ke.math.__init(part, 12)
				part = ke.math.round(math.abs(part))
				part = part < 2 and 2 or part
				local angle = 360 / part
				local ang_b = angle * 0.295927
				local ratio, shp = 1 / math.cos(math.rad(ang_b)), ""
				if type(radius) == "number" then
					for i = 1, part do
						local x0, y0 = ke.math.polar(angle * (i - 1), radius)
						local x1, y1 = ke.math.polar(angle * (i - 1) + ang_b, radius * ratio)
						local x2, y2 = ke.math.polar(angle * i - ang_b, radius * ratio)
						local x3, y3 = ke.math.polar(angle * i, radius)
						shp = shp .. ("m 0 0 l %s %s b %s %s %s %s %s %s l 0 0 "):format(x0, y0, x1, y1, x2, y2, x3, y3)
					end --ke.shape.multi7(12, 100)
				else --type(radius) == "table"
					for i = 1, #radius - 1 do
						for k = 1, part do
							local x0, y0 = ke.math.polar(angle * (k - 1), radius[i + 1])
							local x1, y1 = ke.math.polar(angle * (k - 1) + ang_b, radius[i + 1] * ratio)
							local x2, y2 = ke.math.polar(angle * k - ang_b, radius[i + 1] * ratio)
							local x3, y3 = ke.math.polar(angle * k, radius[i + 1])
							local x4, y4 = ke.math.polar(angle * k, radius[i])
							local x5, y5 = ke.math.polar(angle * k - ang_b, radius[i] * ratio)
							local x6, y6 = ke.math.polar(angle * (k - 1) + ang_b, radius[i] * ratio)
							local x7, y7 = ke.math.polar(angle * (k - 1), radius[i])
							local x8, y8 = ke.math.polar(angle * (k - 1), radius[i + 1])
							shp = shp .. ("m %s %s b %s %s %s %s %s %s l %s %s b %s %s %s %s %s %s l %s %s "):format(
								x0, y0, x1, y1, x2, y2, x3, y3, x4, y4, x5, y5, x6, y6, x7, y7, x8, y8
							)
						end
					end
				end --ke.shape.multi7(12, {20, 40, 60})
				return ke.shape.new(shp):displace({mode = "origin"})
			end,
			
			multi8 = function(self, size1, size2, loop)
				--returns concentric shapes from an initial size to a final size
				local shp = ke.shape.__init(self, ke.shape.rectangle):displace({mode = "origin"})
				size1, size2 = ke.math.__init(size1 or shp.width), ke.math.__init(size2 or shp.width / 2)
				loop = math.abs(math.ceil(type(loop) == "function" and loop() or loop or 8))
				loop = loop < 2 and 2 or loop
				local maxsize = math.max(math.abs(math.ceil(size1)), math.abs(math.ceil(size2)))
				local minsize = math.min(math.abs(math.ceil(size1)), math.abs(math.ceil(size2)))
				local shp1 = shp:size(maxsize, 0)
				local result, c = {}, shp1.centroid
				for i = 1, loop do
					result[i] = shp1:size(maxsize - (maxsize - minsize) * (i - 1) / (loop - 1), 0):displace({x = c.x, y = c.y, mode = "center"}).code
				end
				return ke.shape.new(table.concat(result))
			end, --ke.shape.multi8(ke.shape.rectangle, 100, 10, 10)
			
			to_line = function(self, tract)
				--converts the "bezier" sections of the shape, into "line"
				local self = ke.shape.__init(self)
				tract = type(tract) == "function" and tract() or tract or 5
				return self:redraw(tract, "bezier")
			end, --ke.shape.to_line(ke.shape.circle)
			
			to_bezier = function(self)
				--converts the "line" sections of the shape, into "bezier"
				local self = ke.shape.__init(self)
				local segs, rseg = self:__seg()
				rseg = ke.table.new(segs.n, function(i) return segs[i].t == "l" and segs[i]:to_bezier() or segs[i] end)
				self.code = ke.shape.new(rseg).code
				return self
			end, --ke.shape.to_bezier(ke.shape.rectangle)
			
			insert = function(self, other)
				--modifies the shape code so that it can take the shape of another
				local self, other = ke.shape.__init(self), ke.shape.__init(other)
				local shapes1 = ke.table.new(self.code:gmatch("m[^m]*")) --shapes individuales
				local shapes2 = ke.table.new(other.code:gmatch("m[^m]*"))
				local isolen = function(array1, array2)
					local n1, n2 = #array1, #array2
					array1 = n1 < n2 and array1("newlen", {n2}) or array1
					array2 = n1 > n2 and array2("newlen", {n1}) or array2
					return array1, array2
				end --equalizes the size of two tables
				shapes1, shapes2 = isolen(shapes1, shapes2)
				for i = 1, #shapes1 do
					shapes1[i] = ke.table.new(shapes1[i]:gmatch("[mlb][^mlb]*")) --segmentos de cada shape
					shapes2[i] = ke.table.new(shapes2[i]:gmatch("[mlb][^mlb]*"))
					local m1, m2 = table.remove(shapes1[i], 1), table.remove(shapes2[i], 1)
					shapes1[i], shapes2[i] = isolen(shapes1[i], shapes2[i])
					table.insert(shapes1[i], 1, m1)
					table.insert(shapes2[i], 1, m2)
					for k = 1, #shapes1[i] do
						local t1, t2 = shapes1[i][k]:match("[mbl]"), shapes2[i][k]:match("[mbl]")
						if k > 1 and t1 ~= t2 then
							if t1 == "l" then
								local p0 = ke.shape.point.new(shapes1[i][k - 1]:match("(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)%s?$"))
								local p3 = ke.shape.point.new(shapes1[i][k]:match("(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)%s?$"))
								local p1, p2 = p0:ipol(0.33, {other = p3}), p0:ipol(0.66, {other = p3})
								shapes1[i][k] = ("b %.f %.f %.f %.f %s %s "):format(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
							else
								local p0 = ke.shape.point.new(shapes2[i][k - 1]:match("(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)%s?$"))
								local p3 = ke.shape.point.new(shapes2[i][k]:match("(%-?%d[%.%d]*)%s+(%-?%d[%.%d]*)%s?$"))
								local p1, p2 = p0:ipol(0.33, {other = p3}), p0:ipol(0.66, {other = p3})
								shapes2[i][k] = ("b %.f %.f %.f %.f %s %s "):format(p1.x, p1.y, p2.x, p2.y, p3.x, p3.y)
							end
						end
					end
					shapes1[i], shapes2[i] = table.concat(shapes1[i]), table.concat(shapes2[i])
				end
				self.code = ke.shape.new(table.concat(shapes1)).code
				other.code = ke.shape.new(table.concat(shapes2)).code
				return self, other
			end, --ke.shape.insert(ke.shape.rectangle, ke.shape.circle)
			
			ipol = function(shapes, t, accel, shape, size)
				--returns the interpolation between two or more shapes
				if size then
					return ke.table.new(size, function(i) return ke.shape.ipol(shapes, (i - 1) / (size - 1), accel, shape) end)
				end
				t = ke.math.normalize(t or 0.5, accel, shape)
				if t == 0 then
					return shapes[1]
				end --ke.shape.ipol({ke.shape.rectangle, ke.shape.circle}, 0.7, nil, nil, 15)
				local n = #shapes
				local seg = math.ceil(t * (n - 1))
				local shape1, shape2 = ke.shape.insert(shapes[seg], shapes[seg + 1])
				local pnt1, pnt2 = shape1.pnt, shape2.pnt
				local u = t * (n - 1) - (seg - 1)
				local result = ke.table.new(pnt1.n, function(i) return pnt1[i]:ipol(u, {other = pnt2[i]}) end)
				return ke.shape.new(result).code
			end, --ke.shape.ipol({ke.shape.rectangle, ke.shape.circle}, 0.7)
			
			cut = function(self, t)
				--cuts the shape according to a given parameter t
				local self = ke.shape.__init(self)
				if t < 0 then
					local s, p = ke.shape.cut(self:__inv(), -t)
					return s:__inv(), p
				end
				t = ke.math.clamp(t or 0.5)
				if t == 1 then return self, nil end
				local slength, alength, k = {}, {0}, 1
				local segs = self:__seg()
				for i, s in ipairs(segs) do
					slength[i] = s:length()
					alength[i + 1] = alength[i] + slength[i]
				end
				local tlenght, newsegs = t * self:length(), {}
				for i = 1, #segs do
					newsegs[i] = segs[i]
					if tlenght <= alength[i + 1] then
						k = i
						break
					end
				end
				local newt = slength[k] > 0 and (tlenght - alength[k]) / slength[k] or 0
				newsegs[k] = segs[k]:cut(newt)
				self.code = ke.shape.new(newsegs).code
				return self, segs[k]:parameter(newt)
			end, --ke.shape.cut(ke.shape.rectangle, 0.625)
			
			parameter = function(self, t, n)
				--obtains the point and its angle, corresponding to the parameter t of the shape
				local self = ke.shape.__init(self)
				if n and type(n) == "number" then
					n = math.ceil(math.abs(n))
					local div, posangles = self:__isclosed() and n or n - 1, {}
					return ke.table.new(n, function(i) return {self:parameter((i - 1) / div)} end)
				end
				t = type(t) == "table" and t[1] or t * self:length()
				local seg, length = ke.shape.beziers.length2seg(self, t)
				local nwt = ke.shape.beziers.length2t(seg, length)
				local pos, angle = ke.shape.beziers.config(seg, nwt)
				return pos, angle
			end, --{ke.shape.parameter(ke.shape.new(ke.shape.circle), 0.125)}
			
			getpoint = function(self, t)
				--obtains the point and its angle, corresponding to the parameter t of the shape
				return ke.shape.parameter(self, t)
			end,
			
			getparameter = function(self, p)
				--given a point, it obtains the parameter t, if that point is on the perimeter of the shape
				local self = ke.shape.__init(self):__closed()
				local perimeter = self:length()
				self = self:__unclosed()
				local accum = 0
				for _, s in ipairs(self) do
					local pnt, n = s:points(), s.n
					for i = 1, n do
						local p1 = pnt[i]
						local p2 = (i == n) and pnt[1] or pnt[i + 1]
						local seg = p1:distance(p2)
						if p == p1 then return accum / perimeter end
						local dist1, dist2 = p1:distance(p), seg
						if math.abs(dist1 + p:distance(p2) - dist2) < EPSILON then
							return (accum + dist1) / perimeter
						end
						accum = accum + seg
					end
				end
				return nil
			end, --ke.shape.getparameter("m 0 0 l 0 30 l 30 30 l 30 0 l 0 0 m 10 10 l 20 10 l 20 20 l 10 20 l 10 10 ", ke.shape.point.new(10, 20))
			
			line = function(self, bord, mode)
				--converts the shape perimeter into a linear shape
				local self = ke.shape.__init(self)
				bord = bord and 0.5 * math.abs(bord) or 4
				mode = mode or "miter" --"miter", "round" or "bevel"
				self = self:__red()
				local result, rat = "", 0.115
				for i, s in ipairs(self) do
					local pnt, n = s:points(), s.n
					local exterior, interior = ke.table.new(), ke.table.new()
					local first = pnt[1] == pnt[n] and pnt[n - 1] or pnt[1]:polar(pnt[2]:angle(pnt[1]), 1)
					local last  = pnt[1] == pnt[n] and pnt[2] or pnt[n]:polar(pnt[n - 1]:angle(pnt[n]), 1)
					for k = 1, n do
						local p0 = k == 1 and first or pnt[k - 1]
						local p1, p2 = pnt[k], k == n and last or pnt[k + 1]
						local ang1, ang2 = p0:bisector(p1, p2), p0:angle(p1, p2)
						local radius = math.abs(bord / math.sin(math.rad(ang1 - p1:angle(p0) - (ang2 <= 300 and 0 or rat) * ang2)))
						exterior:insert(ang2 <= 300 and p1:polar(ang1,  radius) or p1:polar(ang1 - rat * ang2,  radius))
						interior:insert(ang2 <= 300 and p1:polar(ang1, -radius) or p1:polar(ang1 - rat * ang2, -radius))
						if ang2 > 300 and k ~= n then
							exterior:insert(p1:polar(ang1 + rat * ang2,  radius))
							interior:insert(p1:polar(ang1 + rat * ang2, -radius))
						end
					end
					exterior = ke.shape.new(exterior)
					interior = ke.shape.new(interior):__inv()
					local ratio = mode == "round" and 2.4 or 1.8
					if s:isclockwise() and mode ~= "miter" then
						interior = interior:roundout(ratio * bord, mode)
					elseif not s:isclockwise() and mode ~= "miter" then
						exterior = exterior:roundout(ratio * bord, mode)
					end
					interior = not s:__isclosed() and interior.code:gsub("m", "l") or interior.code
					result = result .. exterior.code .. interior
				end
				return ke.shape.new(result)
			end, --ke.shape.line("m 0 0 l 0 56 l 44 56 l 44 0 l 0 0 m 15 18 l 87 18 l 87 37 l 15 37 l 15 18 ", 4, "miter")
			
			offset = function(self, bord, mode)
				--converts the shape perimeter into a linear shape
				bord = bord or 6
				local self = ke.shape.__init(self)
				if mode == "round" or mode == "bevel" then
					local radius = bord * 1.48
					return self:roundout(radius, mode):line(bord)
				end
				return self:line(bord) --"miter"
			end, --ke.shape.offset("m 0 0 l 24 6 l 48 -7 l 65 16 l 50 30 l 43 12 l -12 26 ", 5, "bevel")
			
			expand = function(self, pixel)
				--expands the shape taking into account the direction of its path
				local self = ke.shape.__init(self)
				pixel = ke.math.__init(pixel, 4)
				local result = ""
				for i, s in ipairs(self:__red()) do
					local path, pnt, n = ke.table.new(), s:points(), s.n
					local first = pnt[1] == pnt[n] and pnt[n - 1] or pnt[1]:polar(pnt[2]:angle(pnt[1]), 1)
					local last  = pnt[1] == pnt[n] and pnt[2] or pnt[n]:polar(pnt[n - 1]:angle(pnt[n]), 1)
					for k = 1, n do
						local p0 = k == 1 and first or pnt[k - 1]
						local p1, p2 = pnt[k], k == n and last or pnt[k + 1]
						local angle = p0:bisector(p1, p2)
						local radius = pixel / math.sin(math.rad(angle - p1:angle(p0)))
						path:insert(p1:polar(angle, radius))
					end
					result = result .. ke.shape.new(path)
				end
				self.code = result.code
				return self
			end, --ke.shape.expand(ke.shape.rectangle, 6)
			
			pixels = function(self)
				--gets the surface pixels of a shape
				local self = ke.shape.__init(self)
				local upscale = 8
				local downscale = 1 / upscale
				self = self:ratio(upscale)
				local x1, y1, x2, y2 = self:bounding()
				local shift_x, shift_y = -(x1 - x1 % upscale), -(y1 - y1 % upscale)
				self = self:displace({x = shift_x, y = shift_y})
				local function render(shp, width, height, image)
					local line, n, last, move = {}, 0
					shp = shp:__copy():redraw(upscale, "bezier")
					local y1, y2 = shp.miny, shp.maxy
					shp = shp:gsub(
						function(x, y)
							x, y = ke.math.round(x), ke.math.round(y)
							if last and last[2] ~= y and not (last[2] < 0 and y < 0)
								and not (last[2] > height and y > height) then
								n = n + 1
								line[n] = {last[1], last[2], x - last[1], y - last[2]}
							end
							last = {x, y}
						end
					)
					local function hline(x, y, vx, vy, y2)
						if vy ~= 0 then
							local s = (y2 - y) / vy
							if s >= 0 and s <= 1 then
								return x + s * vx, y2
							end
						end
					end
					local function trim (x, min, max)
						return x < min and min or x > max and max or x
					end
					for y = math.max(math.floor(y1), 0), math.min(math.ceil(y2), height) - 1 do
						local row_stops, row_stops_n = {}, 0
						for i = 1, n do
							local line = line[i]
							local cx = hline(line[1], line[2], line[3], line[4], y + 0.5)
							if cx then
								row_stops_n = row_stops_n + 1
								row_stops[row_stops_n] = {trim(cx, 0, width), line[4] > 0 and 1 or -1}
							end
						end
						if row_stops_n > 1 then
							table.sort(row_stops, function(a, b) return a[1] < b[1] end)
							local status, row_index = 0, 1 + y * width
							for i = 1, row_stops_n - 1 do
								status = status + row_stops[i][2]
								if status ~= 0 then
									for x = math.ceil(row_stops[i][1] - 0.5), math.floor(row_stops[i + 1][1] + 0.5) - 1 do
										image[row_index + x] = true
									end
								end
							end
						end
					end
				end
				local img_width  = math.ceil((x2 + shift_x) * downscale) * upscale
				local img_height = math.ceil((y2 + shift_y) * downscale) * upscale
				local img_data = {}
				for i = 1, img_width * img_height do
					img_data[i] = false
				end
				render(self, img_width, img_height, img_data)
				local pixels, pixels_n, opacity = {}, 0
				for y = 0, img_height - upscale, upscale do
					for x = 0, img_width - upscale, upscale do
						opacity = 0
						for yy = 0, upscale - 1 do
							for xx = 0, upscale - 1 do
								if img_data[1 + (y + yy) * img_width + (x + xx)] then
									opacity = opacity + 255
								end
							end
						end
						if opacity > 0 then
							pixels_n = pixels_n + 1
							pixels[pixels_n] = {
								["a"] = ke.alpha.ass(255 - opacity * downscale ^ 2),	--alpha
								["x"] = (x - shift_x) * downscale + 1,					--x coor
								["y"] = (y - shift_y) * downscale + 1					--y coor
							}
						end
					end
				end
				return pixels
			end, --ke.shape.pixels("m 0 0 l 0 5 l 5 5 l 5 0 ")
			
			tensor = function(self, inbox, t)
				--shape modifies respect to its bounding box
				local self = ke.shape.__init(self)
				local P0, P1, P2, P3 = self:box()
				t = t or 1
				inbox = inbox or ke.shape.new(ke.shape.rectangle):size(self.width, self.height)
				local other = ke.shape.new(inbox)
				local xbox = other:to_bezier():__seg()
				table.remove(xbox, 1)
				xbox[3], xbox[4] = xbox[3]:__inv(), xbox[4]:__inv()
				local sup0, sup1, sup2, sup3 = xbox[4][0], xbox[4][1], xbox[4][2], xbox[4][3] --top
				local inf0, inf1, inf2, inf3 = xbox[2][0], xbox[2][1], xbox[2][2], xbox[2][3] --bottom
				local izq0, izq1, izq2, izq3 = xbox[1][0], xbox[1][1], xbox[1][2], xbox[1][3] --left
				local der0, der1, der2, der3 = xbox[3][0], xbox[3][1], xbox[3][2], xbox[3][3] --right
				local sw, sh, ow, oh = self.width, self.height, other.width, other.height
				local tensor_filter = function(x, y)
					local u, v = My, Mx
					local Pt, Pb = sup0:ipol(u, {other = {sup1, sup2, sup3}}), inf0:ipol(u, {other = {inf1, inf2, inf3}})
					local Pl, Pr = izq0:ipol(v, {other = {izq1, izq2, izq3}}), der0:ipol(v, {other = {der1, der2, der3}})
					local vert, hori = Pt:ipol(v, {other = Pb}) * (sw / ow), Pl:ipol(u, {other = Pr}) * (sh / oh)
					x, y = x + (hori.x - x) * t, y + (vert.y - y) * t
					return x, y
				end
				return self:gsub(tensor_filter)
			end, --ke.shape.new(ke.shape.rectangle):redraw(4):tensor("m 0 0 b 5 14 -11 32 0 40 b 10 34 28 34 40 40 b 47 28 47 13 40 0 b 27 -22 13 17 0 0 ")
			
			distort = function(self, other, t, source, target)
				--distorts a shape until it takes the form of another
				local self, other = ke.shape.__init(self), ke.shape.__init(other)
				local oself = self:__copy()
				local funct = {convex = ke.shape.inconvex, boundary = ke.shape.inboundary}
				source, target = source or "convex", target or "boundary"
				self, other = self:redraw(4), other:__red()
				t = t or 1
				local points, centroid = self:points(), self.centroid
				for i, p in ipairs(points) do
					local angle, dis = centroid:topolar(p)
					local _, radius1 = funct[source](oself, angle)
					local _, radius2 = funct[target](other, angle)
					if not radius2 then
						_, radius2 = funct[target](other, -angle)
					end
					points[i] = centroid:polar(angle, dis + (dis * radius2 / radius1 - dis) * t)
					points[i].t = p.t
				end
				self.code = ke.shape.new(points):__red().code
				return self
			end, --ke.shape.distort(ke.shape.rectangle, ke.shape.heart, 0.75)
			
			flexor = function(self, anycurve, t, axis)
				--stretches the shape so that it takes the form of a given curve
				local self = ke.shape.__init(self)
				self = axis == "y" and self:rotate(-90) or self
				local h = self.height
				anycurve = ke.shape.new(anycurve):cut(t or 1)
				local flexor_filter = function(x, y)
					local p, a = anycurve:parameter(My)
					local newp = p:polar(a, h / 2 - y)
					x, y = newp.x, newp.y
					return x, y
				end
				local split = ke.math.round(self:length() / (0.42 * (h + anycurve:length())), ROUND_NUM)
				self = self:redraw(split):gsub(flexor_filter)
				return self
			end, --ke.shape.new("m 0 0 l 0 10 l 80 10 l 80 0 l 10 0 l 10 4 l 4 4 l 4 0 l 0 0 "):flexor("m 0 24 b 17 -2 62 36 71 -3 b 76 -34 133 3 78 24 ")
			
			inflated = function(self, t, split, ratio, mode)
				--inflate the shape until it takes on a circular or elliptical shape
				local self = ke.shape.__init(self)
				split, ratio = split or 4, ratio or 1
				self = self:ratio(ratio):redraw(split)
				mode = mode or "circle" -- or "ellipse"
				local result = {}
				for _, s in ipairs(self) do
					local points, centroid = s:points(), s.centroid
					local w, h = s.width, s.height
					local diameter = math.sqrt((w * w + h * h) / 2)
					local r1 = (mode == "circle" and diameter or w) * math.sqrt(2) / 2
					local r2 = (mode == "circle" and diameter or h) * math.sqrt(2) / 2
					for _, p in ipairs(points) do
						local dx, dy = p.x - centroid.x, p.y - centroid.y
						local distance = math.sqrt(dx * dx + dy * dy)
						local newp = {x = p.x, y = p.y, t = p.t}
						if distance > EPSILON then
							local _cos = math.cos(math.atan2(dy, dx))
							local _sin = math.sin(math.atan2(dy, dx))
							local radius = (r1 * r2) / math.sqrt(r2 * r2 * _cos * _cos + r1 * r1 * _sin * _sin)
							local ux, uy = dx / distance, dy / distance
							local newdist = distance * (1 - t) + radius * t
							newp = {x = centroid.x + ux * newdist, y = centroid.y + uy * newdist, t = p.t}
						end
						table.insert(result, ke.shape.point.new(newp))
					end
				end
				self.code = ke.shape.new(result).code
				return self
			end, --ke.shape.inflated(ke.shape.test, 0.8)
			
			trajectory = function(mode, loop, caliber1, caliber2)	
				--returns trajectories with specific characteristics
				local curves = {	
					["bezier"] = function(loop, distance_nim, distance_max)
						--generates a random shape with a stroke in beziers in a fluid way
						loop = ke.math.__init(loop, 8)
						local dmin, dmax = ke.math.__init(distance_nim, 50), ke.math.__init(distance_max, 120)
						local points, xpoints, shp = ke.shape.point.rand(nil, {n = 2 * loop + 1, dx = dmin, dy = dmax, sign = true}), {}, "m 0 0 b "
						for i = 1, #points do
							shp = shp .. points[i]:__str()
							if i < #points - 2 and i % 2 == 0 then
								shp = shp .. ke.shape.segment.new({points[i], points[i + 1]}):parameter(ke.math.rand(0.3, 0.7, 0.01)):__str()
							end
						end
						return ke.shape.new(shp)
					end, --ke.shape.trajectory("bezier")
					
					["path"] = function(loop, length_total, height_curve) --Curve in Line Trajectory
						--generates a random shape with a stroke in beziers in a fluid way, in a straight path
						local lengthT, ratio = ke.math.__init(length_total, 640), ke.math.__init(height_curve, 30)
						local lengthC = lengthT / ke.math.__init(loop, 4)
						local n, points, sign, x, y = ke.math.round(lengthT / lengthC), {}, (-1) ^ ke.math.rand(2)
						local xray, shp = ke.shape.segment.new({-lengthC, 0, n * lengthC + lengthC, 0}), "m 0 0 b "
						local cix, ciy = ke.math.count(2), ke.math.count()
						for i = 1, 2 * n do
							x = lengthC * (cix("N,n", 2) - 1) + ke.math.rand(0.35 * lengthC, 0.65 * lengthC) * sign ^ i
							y = ratio * sign * (-1) ^ ciy("N,n", 2) + ke.math.rand(1, 0.125 * ratio, 1, true)
							points[#points + 1] = ke.shape.point.new(x, y)
						end
						points[#points + 1] = ke.shape.point.new(n * lengthC + ke.math.rand(1, 0.125 * lengthC, 1, true), 0)
						for i = 1, #points do
							shp = shp .. points[i]:__str()
							if i < #points - 2 and i % 2 == 0 then
								shp = shp .. xray:intersect({points[i], points[i + 1]}):__str()
							end
						end
						return ke.shape.new(shp)
					end, --ke.shape.trajectory("path").code
					
					["line"] = function(loop, radius) --Segment Line Trajectory
						--generate a random shape with straight strokes
						loop, radius = ke.math.__init(loop, 8), ke.math.__init(radius, 60)
						local loops, angles = math.ceil(loop), {[0] = ke.math.rand(36) * 10}
						for i = 1, loops do
							angles[i] = ke.math.rand(angles[i - 1] + 110, angles[i - 1] + 250)
						end
						local shp, Rand = "m 0 0 "
						for i = 1, loops do
							Rand = ke.math.rand(0.7 * radius, radius)
							shp = shp .. ("l %s %s "):format(ke.math.polar(angles[i], Rand))
						end
						return ke.shape.new(shp)
					end, --ke.shape.trajectory("line").code
				}
				local mode = mode or "bezier"
				return curves[mode] and curves[mode](loop, caliber1, caliber2) or curves["bezier"](loop, caliber1, caliber2)
			end,
			
			to_clip = function(self, x, y, iclip)
				--converts a shape into a vector clip
				local self = ke.shape.__init(self)
				local fx = ke.infofx.data.fx
				local shp = self:displace({x = x or fx.x, y = y or fx.y, mode = "center"}).code
				return ("\\%sclip(%s)"):format(iclip and "i" or  "", shp)
			end, --ke.shape.to_clip(ke.shape.circle)
			
			divide = function(self)
				--array of shapes that make up a shape
				local self = ke.shape.__init(self)
				local x1, y1, x2, y2 = self:bounding()
				local mark = ("m %s %s l %s %s m %s %s l %s %s "):format(x1, y1, x2, y1, x1, y2, x2, y2)
				local shapes = {}
				for i, s in ipairs(self) do
					shapes[i] = mark .. s.code
				end --ke.shape.divide({"m 50 53 l 23 66 m 50 53 l 54 84 ", "m 0 5 l 2 6 m 5 3 l 5 8 "})
				return shapes
			end, --ke.shape.divide("m 50 53 l 23 66 l 20 96 l 46 84 m 50 53 l 54 84 l 81 97 l 78 66 ")
			
			fusion = function(shapes, tags)
				--merge the entered shapes so that they occupy a single fx line
				shapes = ke.shape.__init(shapes, {ke.shape.rectangle, ke.shape.circle})
				tags = type(tags) == "function" and tags() or tags
				local aux = not shapes.code and ke.table.iter(nil, function(i, v, s) return s .. ke.shape.new(shapes[i]) end, {start = "", i = {1, #shapes}}) or nil
				shapes = aux or shapes
				local w, h = shapes.width, shapes.height
				shapes = shapes:displace({mode = "origin"}):divide()
				local result, n = "", #shapes
				tags = tags or ke.table.new(n, function() return ("\\1c%s"):format(ke.color.random(nil, 0.82)) end)
				for i = n, 1, -1 do
					shapes[i] = ke.shape.displace(shapes[i], {x = 0.5 * w + (n - i) * w, y = 0.5 * h, mode = "center"})
					shapes[i] = shapes[i]:displace({x = -0.5 * n * w + 0.5 * w})
				end
				for i = 1, n do
					shapes[i] = "{" .. tags[(i - 1) % #tags + 1] .. "}" .. shapes[i].code
					result = result .. shapes[i]
				end
				return result
			end, --ke.shape.fusion({"m 0 0 l 0 40 l 10 40 l 10 0 m 10 0 l 10 40 l 20 40 l 20 0 m 20 0 l 20 40 l 30 40 l 30 0 "})
			
			graph = {
				polygon = function(n, radius, angle, bord)
					--creates regular polygons with specific characteristics
					n = type(n) == "function" and n() or n or 6
					n = math.abs(math.ceil(n < 3 and 3 or n))
					radius, angle = radius or 50, angle
					local do_polygon = function(n, radius, angle, bord)
						if not n or n == math.huge then
							local poly = ke.shape.new(ke.shape.circle):size(2 * radius):rotate(-90, "center"):displace({mode = "center"})
							poly = angle and poly:cut(angle / 360) or poly
							poly = (bord and type(bord) == "number") and poly:line(bord) or poly
							return poly.code
						end --ke.shape.graph.polygon(nil, {40, 50}, 300, 5)
						local anglex, thetax = 360 / n, 90 * (n - 2) / n
						local poly = ""
						for i = 1, n + 1 do
							poly = poly .. ("l %s %s "):format(ke.math.polar(anglex * (i - 1), radius))
						end
						poly = poly:gsub("l", "m", 1)
						if n % 2 == 1 then --n impar
							local anglix = 90 - anglex * math.floor(90 / anglex)
							local fakex = radius * math.sin(math.rad(thetax)) / math.sin(math.rad(180 - thetax - anglix))
							poly = ("m %s 0 "):format(fakex)
							for i = 1, n do
								poly = poly .. ("l %s %s "):format(ke.math.polar(anglix + anglex * (i - 1), radius))
							end
							poly = poly .. ("l %s 0 "):format(fakex)
						end
						poly = ke.shape.new(poly)
						poly = angle and poly:cut(angle / 360) or poly
						poly = (bord and type(bord) == "number") and poly:line(bord) or poly
						return poly.code
					end --ke.shape.graph.polygon(8, {40, 50}, 300, 5)
					radius = type(radius) ~= "table" and {radius} or radius
					angle = (angle and type(angle) ~= "table") and {angle} or angle
					local polygon = ""
					for i = 1, #radius do
						polygon = polygon .. do_polygon(n, radius[i], angle and angle[(i - 1) % #angle + 1], bord)
					end
					return polygon
				end,
				
				banner = function(width, height, mode, bord)
					--creates banners with specific characteristics
					width, height = ke.math.__init(width, 200), ke.math.__init(height, 50)
					mode = type(mode) == "function" and mode() or mode or "[]"
					bord = type(bord) == "function" and bord() or bord
					local heads = {
						[1] = {--banner start
							["["] = "m 0 0 l 0 100 ",									["]"] = "m 0 0 l 0 100 ",
							["<"] = "m 28.86 0 l 0 50 l 28.86 100 ",					[">"] = "m 0 0 l 28.86 50 l 0 100 ",
							["/"] = "m 28.86 0 l 0 100 ",								["\\"] = "m 0 0 l 28.86 100 ",
							["{"] = "m 27 0 l 15 12 15 35 0 50 15 65 15 88 27 100 ",	["}"] = "m 0 0 l 12 12 12 35 27 50 12 65 12 88 0 100 ",
							["="] = "m 0 0 l 0 32 32 32 32 68 0 68 0 100 ",				["#"] = "m 0 0 l 0 20 20 20 20 40 0 40 0 60 20 60 20 80 0 80 0 100 ",
							["("] = "m 50 0 b 22 0 0 22 0 50 b 0 78 22 100 50 100 ",
							[")"] = "m 0 0 b 17.591 9.974 28.88 28.447 28.88 50 b 28.88 71.553 17.591 90.026 0 100 ",
						},
						[2] = {--banner end
							["]"] = "m 0 100 l 0 0 ",									["["] = "m 0 100 l 0 0 ",
							["<"] = "m 0 100 l -28.86 50 l 0 0 ",						[">"] = "m -28.86 100 l 0 50 l -28.86 0 ",
							["/"] = "m -28.86 100 l 0 0 ",								["\\"] = "m 0 100 l -28.86 0 ",
							["}"] = "m 0 100 l 12 88 12 65 27 50 12 35 12 12 0 0 ",		["{"] = "m 0 100 l -12 88 -12 65 -27 50 -12 35 -12 12 0 0 ",
							["="] = "m 0 100 l 0 68 -32 68 -32 32 0 32 0 0 ",			["#"] = "m 0 100 l 0 80 -20 80 -20 60 0 60 0 40 -20 40 -20 20 0 20 0 0 ",
							[")"] = "m -50 100 b -22 100 0 78 0 50 b 0 22 -22 0 -50 0 ",
							["("] = "m 0 100 b -17.591 90.026 -28.88 71.553 -28.88 50 b -28.88 28.447 -17.591 9.974 0 0 ",
						} --ke.shape.graph.banner(600, 100, "#{", 4)
					} --ke.shape.graph.banner(300, 40, "<]")
					mode = (type(mode) ~= "string" and type(mode) ~= "table") and "[]" or mode
					local mode_i = type(mode) == "string" and mode:sub(1, 1) or mode[1] or "["
					local mode_f = type(mode) == "string" and mode:sub(2, 2) or mode[2] or "]"
					local ini = ke.shape.new(heads[1][mode_i] or mode_i or "m 0 0 l 0 100 ")
					local fin = ke.shape.new(heads[2][mode_f] or mode_f or "m 0 100 l 0 0 ")
					ini = ini:ratio(nil, {height})
					fin = fin:ratio(nil, {height}):displace({x = width})
					local banner = ini.code .. fin.code:gsub("m", "l")
					banner = ke.shape.new(banner):to_line():__closed()
					return (bord and type(bord) == "number") and banner:line(bord):displace({mode = "origin"}) or banner:displace({mode = "origin"})
				end, --ke.shape.graph.banner(300, 40, "<>", 4)
				
				gear = function(radius, n, dent, double, bord)
					--creates gears with specific characteristics
					radius = type(radius) == "function" and radius() or radius or 180
					n = type(n) == "function" and n() or n or 8
					local graph_gear = function(radius, n, dent)
						local ratio, angle = 0.38, 360 / n
						local arc1, arc2 = ratio * angle, 0.5 * (1 + ratio) * angle
						local length = 2 * math.pi * radius * angle / 360
						dent = type(dent) == "function" and dent() or dent or "m 0 0 l 100 0 "
						dent = ke.shape.new(dent):rotate({nil, 0}):displace({mode = "center"})
						local height = dent.height
						local parts = {
							[1] = ke.shape.new("m 50 0 b 50 -28 28 -50 0 -50 "):size(radius):cut(arc1 / 90),
							[2] = dent:ratio({0.45 * length}):rotate(90 + arc2):displace({x = arc2, y = radius + 0.45 * length - height / 5, mode = "polar"})
						}
						dent = ke.shape.new(parts[1].code .. parts[2].code:gsub("m", "l"))
						local gear_shp = ""
						for i = 1, n do
							gear_shp = gear_shp .. dent:rotate(angle * (i - 1)).code
						end --ke.shape.graph.gear(100, 8, "m 0 0 l 30 0 l 30 -22 l 70 -22 l 70 0 l 100 0 "):round()
						local result = ke.shape.new(gear_shp):rotate(-arc2).code:gsub("m", "l"):gsub("l", "m", 1)
						return ke.shape.new(result):__closed()
					end
					local cir_1 = ke.shape.new("m 0 -50 b -28 -50 -50 -28 -50 0 b -50 28 -28 50 0 50 b 28 50 50 28 50 0 b 50 -28 28 -50 0 -50 ")
					local cir_2 = cir_1:__inv()
					local circle_add1 = cir_2:size(1.8 * radius) .. cir_1:size(1.5 * radius)
					local circle_add2 = cir_2:size(0.5 * radius)
					local shp_gear = graph_gear(radius, n, dent)
					if double then
						shp_gear = shp_gear .. graph_gear(0.7 * radius, n, dent):__inv()
						circle_add1 = cir_1:size(1.1 * radius) .. cir_2:size(0.9 * radius)
						circle_add2 = cir_1:size(0.5 * radius)
					end
					local gear = shp_gear .. circle_add1 .. circle_add2
					gear = (bord and type(bord) == "number") and gear:line(bord) or gear
					return gear:displace({mode = "origin"})
				end --ke.shape.graph.gear(80, 8, "m -45 -16 l -20 0 l 20 0 l 45 -16 ", true)
			},
			
			inbounding = function(self, angle)
				--point in bounding
				local self = ke.shape.__init(self)
				local box = {self:box()}
				angle = angle or 0
				local centroid = self.centroid
				local p = centroid:polar(angle, self.radius + 10)
				for i = 1, 4 do
					local newp = centroid:intersect(p, box[i], box[i % 4 + 1])
					if newp then
						return newp, newp:distance(centroid)
					end
				end
			end, --ke.shape.inbounding(ke.shape.rectangle, 15)
			
			inboundary = function(self, angle)
				--point in principal boundary shape
				local self = ke.shape.__init(self)
				angle = angle or 0
				for _, s in ipairs(self) do
					local centroid = s.centroid
					local pnt, n = s:points(), s.n
					local p = centroid:polar(angle, s.radius + 10)
					for i = 1, n do
						local newp = centroid:intersect(p, pnt[i], pnt[i % n + 1])
						if newp then
							return newp, newp:distance(centroid)
						end
					end
					break
				end
				return nil
			end, --ke.shape.inboundary(ke.shape.rectangle, 15)
			
			inconvex = function(self, angle)
				--point located on the convex hull of the shape, at a given angle
				local self = ke.shape.__init(self)
				local points = self.pnt
				local convexscan = ke.shape.point.toconvex(points)
				angle = angle or 0
				local centroid = self.centroid
				local p = centroid:polar(angle, self.radius + 10)
				local n = #convexscan
				for i = 1, n do
					local newp = centroid:intersect(p, convexscan[i], convexscan[i % n + 1])
					if newp then
						return newp, newp:distance(centroid)
					end
				end
			end, --ke.shape.inconvex(ke.shape.rectangle, 15)
			
			matrix = function(self, m)
				--applies a transformation through one matrix
				local self = ke.shape.__init(self)
				m = ke.math.matrix.new(m)
				local shapes = {}
				for i, s in ipairs(self) do
					local points = s.pnt
					shapes[i] = ke.shape.new(points:filter(function(i, p) return p * m end)).code
				end
				self.code = ke.shape.new(table.concat(shapes)).code
				return self
			end, --ke.shape.matrix(ke.shape.rectangle, {1, 0, 0, 0, math.sin(45), 0, 0, 0, math.cos(45)})
			
			bars = function(self, tags, vertical)
				--redraws the shape into individual vertical or horizontal bars
				local self = ke.shape.__init(self)
				self = self:redraw(4, "bezier")
				local x0, y0, x1, y1 = self:bounding()
				local angle = ke.math.rand(360)
				tags = tags or function(i, n) return ("\\1c%s"):format(ke.color.HSV_to_RGB(angle + 90 * i / n)) end --example
				local exteriors, holes = {}, {} --ass format
				for _, s in ipairs(self) do
					table.insert(s:isclockwise() and holes or exteriors, s:points())
				end
				local v, helpers = vertical
				helpers = {
					inside = function(p, poly)
						local result = false
						local j = #poly
						for i = 1, #poly do
							local pi, pj = poly[i], poly[j]
							if ((pi.y > p.y) ~= (pj.y > p.y)) and
								(p.x < (pj.x - pi.x) * (p.y - pi.y) / ((pj.y - pi.y) + EPSILON) + pi.x) then
								result = not result
							end
							j = i
						end
						return result
					end,
					
					getbars = function(pixels)
						local fsort = v and function(p, q) return p.x == q.x and p.y < q.y or p.x < q.x end --"vertical"
							or function(p, q) return p.y == q.y and p.x < q.x or p.y < q.y end --"horizontal"
						table.sort(pixels, fsort)
						local bars, current, ini, fin = {}, nil, nil, nil
						for i, p in ipairs(pixels) do
							local fixed, axis = v and p.x or p.y, v and p.y or p.x
							if fixed ~= current or (fin and axis ~= fin + 1) then
								if ini then
									table.insert(bars, {x = v and current or ini, y = v and ini or current, l = fin - ini + 1})
								end
								current, ini = fixed, axis
							end
							fin = axis
						end
						if ini and fin then
							table.insert(bars, {x = v and current or ini, y = v and ini or current, l = fin - ini + 1})
						end
						return bars
					end,
					
					bargroup = function(pixels)
						local bars = helpers.getbars(pixels)
						local groups = {}, {}
						for _, b in ipairs(bars) do
							local key = v and b.x or b.y
							if not groups[key] then
								groups[key] = {b}
							else
								table.insert(groups[key], b)
							end				
						end
						return ke.table.get(groups, "idx")
					end,
					
					bars2shape = function(pixels)
						local bars = helpers.bargroup(pixels)
						local n = #bars
						bars[0] = {{x = x0 - 1, y = y0 - 1}}
						local shapes, shp = {}, "%s %s %s %s %s %s %s %s "
						for i, bar in ipairs(bars) do
							shapes[i] = ("bars m %s %s l "):format(x0, y0)
							local nx, ny, add
							if v then
								for k, b in ipairs(bar) do
									ny = not ny and b.y or ny
									nx = b.x - bars[i - 1][1].x - 1
									shapes[i] = shapes[i] .. shp:format(nx, b.y, nx + 1, b.y, nx + 1, b.y + b.l, nx, b.y + b.l)
								end
							else
								for k, b in ipairs(bar) do
									nx = not nx and b.x or nx
									ny = b.y - bars[i - 1][1].y - 1
									shapes[i] = shapes[i] .. shp:format(b.x, ny, b.x, ny + 1, b.x + b.l, ny + 1, b.x + b.l, ny)
								end
							end
							add = v and ("%s %s %s %s "):format(nx, y1, nx, ny) or ("%s %s %s %s "):format(x1, ny, nx, ny)
							shapes[i] = ("{%s\\p1}"):format(type(tags) == "function" and tags(i, n) or tags) .. shapes[i] .. add
							shapes[i] = shapes[i]:gsub("(%d+ %d+) l (%d+ %d+)", function(p, q) return p == q and p .. " l" or p .. " l " .. q end)
							shapes[i] = shapes[i] .. (not v and "{\\p0}\\N" or "")
						end
						return table.concat(shapes)
					end
				}
				local pixels = {}
				for y = math.floor(y0), math.ceil(y1) do
					for x = math.floor(x0), math.ceil(x1) do
						local total = 0
						local p = ke.shape.point.new(x + 0.5, y + 0.5)
						local isinside, ec, hc = false, 0, 0
						for _, ext in ipairs(exteriors) do
							if helpers.inside(p, ext) then
								isinside = true
								ec = ec + 1
							end
						end
						if isinside then
							for _, h in ipairs(holes) do
								if helpers.inside(p, h) then
									hc = hc + 1
								end
							end
						end
						isinside = isinside and ((hc > 0 and (ec + hc) % 2 == 1) and true or (hc == 0 and true or false)) or false
						if isinside then
							total = total + 1
						end
						if total > 0 then
							table.insert(pixels, {x = x, y = y})
						end
					end
				end
				return helpers.bars2shape(pixels)
			end, --ke.shape.bars("m 0 0 l 0 60 l 60 60 l 60 0 l 0 0 m 20 20 l 40 20 l 40 40 l 20 40 l 20 20 ")
			
			splitmove = function(self)
				local self = ke.shape.__init(self)
				local segs = self:__seg()
				local result = ke.table.new()
				for _, s in ipairs(segs) do
					if s.t == "m" then
						result:insert(s)
					elseif s.t == "l" then
						local x0, y0, x1, y1 = s[0].x, s[0].y, s[1].x, s[1].y
						if y0 * y1 < 0 then
							local p = ke.shape.point.new(x0 + (-y0 / (y1 - y0)) * (x1 - x0), 0)
							result:insert(ke.shape.segment.new({s[0], p}))
							result:insert(ke.shape.segment.new({p, s[1]}))
						else
							result:insert(s)
						end
					elseif s.t == "b" then
						local _, yroots = ke.shape.beziers.roots(s)
						local curve, ini, c1, c2 = s, 0
						for _, t in ipairs(yroots) do
							local u = (t - ini) / (1 - ini)
							c1, c2 = curve:cut(u)
							ini = t
							result:insert(c1)
							curve = c2
						end
						result:insert(c2 or s)
					end
				end
				self.code = ke.shape.new(result).code
				return self
			end, --ke.shape.splitmove("m 0 9 b 20 -11 40 -11 60 9 "):round()
			
		},
		
		color = {
			
			ass = function(R, G, B)
				--xy-vsfilter format color
				R, G, B = ke.math.__init(R, 255), ke.math.__init(G, 255), ke.math.__init(B, 255)
				if type(R) == "table" then
					R, G, B = R[1], R[2], R[3]
				end
				local color
				if type(R) == "string" and R:match("%x%x%x%x%x%x") then
					color = R:gsub("%#(%x%x)(%x%x)(%x%x)", "&H%3%2%1&")				--HTML to ass
					:gsub("%x%x(%x%x%x%x%x%x)", "&H%1&")							--color fromstyle
					color = "&H" .. R:match("[%&Hh]*(%x%x%x%x%x%x)[%&]*") .. "&"	--from error
				elseif type(R) == "number" then
					local iR, iG, iB = ke.math.count(R + 1), ke.math.count(G + 1), ke.math.count(B + 1)
					R, G, B = iR("ABA", 0, 255), iG("ABA", 0, 255), iB("ABA", 0, 255)
					color = ("&H%02X%02X%02X&"):format(B, G, R)
				end
				return color --ke.color.ass("#AA00FF")
			end,
			
			to_RGB = function(color)
				--returns a table with the RGB values ​​of the entered color
				color = ke.color.ass(color or "&HFFFFFF&")
				local B, G, R = color:match("(%x%x)(%x%x)(%x%x)")
				return {tonumber(R, 16), tonumber(G, 16), tonumber(B, 16)}
			end, --ke.color.to_RGB("&HAAF0B7&")
			
			to_HSV = function(color)
				--returns a table with the HSV values ​​of the entered color
				color = ke.color.ass(color or "&HFFFFFF&")
				local R, G, B = table.unpack(ke.color.to_RGB(color))
				R, G, B = R / 255 + 0.000001, G / 255, B / 255
				local cmax, cmin = math.max(R, G, B), math.min(R, G, B)
				local dval = cmax - cmin
				local H = cmax == R and ke.math.round(60 * (((G - B) / dval) % 6), 3)
				or (cmax == G and ke.math.round(60 * (((B - R) / dval) + 2), 3))
				or ke.math.round(60 * (((R - G) / dval) + 4), 3)
				local S, V = ke.math.round(dval / cmax, 3), ke.math.round(cmax, 3)
				return {H, S, V}
			end, --ke.color.to_HSV("&HAAF0B7&")
			
			HSV_to_RGB = function(H, S, V)
				--HSV to ass color format
				H, S, V = ke.math.__init(H, 0), ke.math.__init(S, 1), ke.math.__init(V, 1)
				if type(H) == "table" then
					V, S, H = H[3], H[2], H[1]
				end
				H, S, V = ((H - 1) % 360 + 1) / 360 * 6, ((1000 * S) % 1001) / 1000, ((1000 * V) % 1001) / 1000
				if S == 0 or V == 0 then
					return S == 0 and "&HFFFFFF&" or "&H000000&"
				end
				local C = V * S
				local M = V - C
				local X = C * (1 - math.abs((H % 2) - 1))
				local R = H < 1 and C or H < 2 and X or H < 3 and 0 or H < 4 and 0 or H < 5 and X or C
				local G = H < 1 and X or H < 2 and C or H < 3 and C or H < 4 and X or H < 5 and 0 or 0
				local B = H < 1 and 0 or H < 2 and 0 or H < 3 and X or H < 4 and C or H < 5 and C or X
				return ke.color.ass(255 * (R + M), 255 * (G + M), 255 * (B + M))
			end, --ke.color.HSV_to_RGB(128, 1, 1)
			
			random = function(H, S, V)
				--generates a random color with specific parameters
				H, S, V = ke.math.__init(H, ke.math.rand(360)), ke.math.__init(S, 1) * 100, ke.math.__init(V, 1) * 100
				local iS, iV = ke.math.count(S + 1), ke.math.count(V + 1)
				H = type(H) == "table" and ke.math.rand((H[1] - 1) % 360 + 1, (H[2] - 1) % 360 + 1)
				or (type(H) == "number" and (H - 1) % 360 + 1) or ke.math.rand(360)
				S = type(S) == "table" and ke.math.rand(S[2] % 101, S[1] % 101) / 100
				or (type(S) == "number" and iS("ABA", 0, 100) / 100) or 1
				V = type(V) == "table" and ke.math.rand(V[2] % 101, V[1] % 101) / 100
				or (type(V) == "number" and iV("ABA", 0, 100) / 100) or 1
				return ke.color.HSV_to_RGB(H, S, V)
			end, --ke.color.random()
			
			ipol = function(colors, t, accel, shape, size)
				--returns the interpolation between two or more colors
				if size then
					return ke.table.new(size, function(i) return ke.color.ipol(colors, (i - 1) / (size - 1), accel, shape) end)
				end
				t = ke.math.normalize(t or 0.5, accel, shape)
				if t == 0 then return colors[1] end
				local n = #colors
				local seg = math.ceil(t * (n - 1))
				local color1, color2 = ke.color.ass(colors[seg]), ke.color.ass(colors[seg + 1])
				local u = t * (n - 1) - (seg - 1)
				local B1, G1, R1 = color1:match("(%x%x)(%x%x)(%x%x)")
				local B2, G2, R2 = color2:match("(%x%x)(%x%x)(%x%x)")
				R1, G1, B1 = tonumber(R1, 16), tonumber(G1, 16), tonumber(B1, 16)
				R2, G2, B2 = tonumber(R2, 16), tonumber(G2, 16), tonumber(B2, 16)
				local R, G, B = ke.math.round(R1 + (R2 - R1) * u), ke.math.round(G1 + (G2 - G1) * u), ke.math.round(B1 + (B2 - B1) * u)
				return ke.color.ass(R, G, B)
			end, --ke.color.ipol({"&H000000&", ke.color.random(), ke.color.random()}, 0.7)
			
			set = function(times, colors, ...)
				--returns color transformations (\\t) at specified times
				times = type(times) == "function" and times() or times
				colors = ke.color.ass(type(colors) == "function" and colors() or colors)
				local concats = {...} --... = \\1c, \\3c or \\4c
				local fx = ke.infofx.data.fx
				concats = #concats == 0 and {"\\1c"} or concats
				times = ke.table.new(ke.time.HMS_to_ms(times))
				times:insert({fx.time_ini, fx.time_fin}, nil, true)
				times = times("org")
				local times2 = ke.table.copy(times)
				local ini, fin = ke.table.index(times, fx.time_ini), ke.table.index(times, fx.time_fin)
				colors[0] = #colors >= #times - 1 and colors[#times - 1] or "&HFFFFFF&"
				local t1, t2, offset, accel, idx = 0, 1, 1, 1, ini + 1
				for i = 0, #colors do
					colors[i] = type(colors[i]) == "function" and colors[i]() or colors[i]
					colors[i] = type(colors[i]) == "table" and colors[i][(fx.i - 1) % #colors[i] + 1] or colors[i]
					local tagcolor = ""
					for k = 1, #concats do
						tagcolor = tagcolor .. concats[k] .. colors[i]
					end
					colors[i] = tagcolor
				end
				local tags = colors[idx - 2]
				for i = 1, #times do
					times[i] = type(times[i]) == "table" and times[i][1] or times[i]
				end
				if ini + 1 ~= fin then
					while times[idx] < fx.time_fin do
						offset = type(times2[idx]) == "table" and times2[idx][2] or offset
						accel  = type(times2[idx]) == "table" and times2[idx][3] or 1
						t1 = ke.math.clamp(times[idx] - fx.time_ini - 20, 0, math.huge)
						t2 = t1 + offset
						tags = tags .. ("\\t(%s,%s,%s,%s)"):format(t1, t2, accel, colors[idx - 1])
						idx, offset = idx + 1, 1
					end --timex = {"0:00:59.101", "0:01:02.145", "0:01:04.147"}; colorx = {"&H00FFFF&", "&HB82913&", "&H0C0DF7&"}
				end
				return tags --ke.color.set(timex, colorx, "\\1c")
			end,
			
		},
		
		alpha = {
			
			ass = function(alpha, number)
				--formats the alphas with xy-vsfilter
				alpha = ke.math.__init(alpha, 0)
				if type(alpha) == "table" then
					return ke.table.recurse(ke.alpha.ass, alpha, number)
				end --recurse
				alpha = type(tonumber(alpha)) == "number" and ("%X"):format(math.ceil(alpha) % 256)
				or ((type(alpha) == "string" and alpha:match("[&H]*%x%x[&]*")) and alpha:match("[&H]*(%x%x)[&]*")) or alpha
				alpha = (type(alpha) == "string" and alpha:len() == 1) and "0" .. alpha or alpha
				assert(type(alpha) == "string" and alpha:match("(%x%x)"), "Error in alpha.ass: number or alpha expected, got " .. type(alpha))
				alpha = alpha:gsub("(%x+)", "&H%1&") --ke.alpha.ass({x = "(FF,00,AA,0F)", "#F0"})
				return number and tonumber(alpha:match("(%x%x)"), 16) or alpha
			end, --ke.alpha.ass({0, 45, 86, 255})
			
			random = function(alpha1, alpha2)
				--generates an alpha randomly
				alpha1, alpha2 = ke.math.__init(alpha1, 0), ke.math.__init(alpha2, 255)
				alpha1, alpha2 = ke.alpha.ass(alpha1, true), ke.alpha.ass(alpha2, true)
				return ke.alpha.ass(ke.math.rand(alpha2, alpha1))
			end, --ke.alpha.random()
			
			ipol = function(alphas, t, accel, shape, size)
				--returns the interpolation between two or more alphas
				if size then
					return ke.table.new(size, function(i) return ke.alpha.ipol(alphas, (i - 1) / (size - 1), accel, shape) end)
				end
				t = ke.math.normalize(t or 0.5, accel, shape)
				if t == 0 then
					return alphas[1]
				end
				local n = #alphas
				local seg = math.ceil(t * (n - 1))
				local alpha1, alpha2 = ke.alpha.ass(alphas[seg], true), ke.alpha.ass(alphas[seg + 1], true)
				local u = t * (n - 1) - (seg - 1)
				return ke.alpha.ass(alpha1 + u * (alpha2 - alpha1))
			end, --ke.alpha.ipol({"&H00&", ke.alpha.random(), ke.alpha.random()}, 0.7)
			
		},
		
		text = {
			
			to_shape = function(text, scale, without)
				--converts the text into a shape
				text = text or ke.infofx.data.fx.text
				while text:sub(-1, -1) == " " do
					text = text:sub(1, -2)
				end
				scale = scale or 1
				local style = ke.infofx.data.l.style
				if ke.infofx.data.l.text_raw:match("%b{}") then --extract tag settings from line text
					tagx = ke.infofx.data.l.text_raw:match("%b{}")
					style.fontname = tagx:match("\\fn(%S+[^\\]*)") and tagx:match("\\fn(%S+[^\\]*)") or style.fontname
					style.bold = tagx:match("\\b%d") and (tagx:match("\\b(%d)") == "1" and true or false) or style.bold
					style.italic = tagx:match("\\i%d") and (tagx:match("\\i(%d)") == "1" and true or false) or style.italic
					style.underline = tagx:match("\\u%d") and (tagx:match("\\u(%d)") == "1" and true or false) or style.underline
					style.strikeout = tagx:match("\\s%d") and (tagx:match("\\s(%d)") == "1" and true or false) or style.strikeout
					style.fontsize = tagx:match("\\fs(%d[%.%d]*)") and tonumber(tagx:match("\\fs(%d[%.%d]*)")) or style.fontsize
					style.scale_x = tagx:match("\\fscx(%d[%.%d]*)") and tonumber(tagx:match("\\fscx(%d[%.%d]*)")) or style.scale_x
					style.scale_y = tagx:match("\\fscy(%d[%.%d]*)") and tonumber(tagx:match("\\fscy(%d[%.%d]*)")) or style.scale_y
					style.spacing = tagx:match("\\fsp(%-?%d[%.%d]*)") and tonumber(tagx:match("\\fsp(%-?%d[%.%d]*)")) or style.spacing
				end --thank to Zeref Sama
				local configtxt = {
					[1] = style.fontname,				[2] = style.bold,
					[3] = style.italic,					[4] = style.underline,
					[5] = style.strikeout,				[6] = style.fontsize,
					[7] = style.scale_x * scale / 100,	[8] = style.scale_y * scale / 100,
					[9] = style.spacing
				}
				local text_font = ke.decode.create_font(configtxt)
				local text_shape = ke.shape.new(text_font.text_to_shape(text))
				if without then
					return text_shape.code
				end
				local width, height = aegisub.text_extents(style, text)
				local text_off_x = 0.5 * (text_shape.width - scale * width)
				local text_off_y = 0.5 * (text_shape.height - scale * height)
				return text_shape:displace({x = text_off_x, y = text_off_y}).code
			end, --ke.text.to_shape(fx.text)
			
			bezier = function(shp, mode, offset)
				--position and angle of the text on a specified curve
				local l, fx = ke.infofx.data.l, ke.infofx.data.fx
				shp = type(shp) == "function" and shp() or shp
				shp = not shp and l.text_raw:match("\\i?clip%b()") or shp
				shp = type(shp) == "string" and ke.shape.new(shp) or shp
				local offset, lineoffset, blength = offset or 0, 0, shp:length()
				lineoffset = mode == 2 and offset						--alinea el texto desde la izquierda
				or (mode == 3 and blength - l.width - offset)			--alinea el texto desde la derecha
				or (mode == 4 and (blength - l.width) * offset)			--justifica el texto en toda la longitud de la shape: offset = (ci - 1) / (cn - 1)
				or (mode == 5 and (blength - l.width) * (1 - offset))	--anima el texto de fin a inicio de la shape
				or (blength - l.width) / 2 + offset						--modo por default (centro de la shape)(mode == 1)
				--!maxloop(orgline.duration / frame_dur)!!retime("preline", frame_dur * (j - 1), frame_dur * j)!
				--{\an5!_G.ke.text.bezier(line, nil, $x, $y, 5, (j - 1) / (maxj - 1))!}
				local target = lineoffset + fx.center - l.left
				local pos, angle = shp:parameter({target})
				return target > blength and ("\\pos(%s,%s)"):format(fx.center, fx.middle)
				or ("\\pos(%s,%s)\\fr%s"):format(pos.x, pos.y, angle)
			end, --ke.text.bezier("m 108 466 b 310 535 268 297 356 294 566 278 571 474 702 534 917 631 748 109 1140 106")
			
			romaji = {
				"kya",	"kyu",	"kyo",	"sha",	"shu",	"sho",	"cha",	"chu",	"cho",
				"nya",	"nyu",	"nyo",	"hya",	"hyu",	"hyo",	"mya",	"myu",	"myo",
				"rya",	"ryu",	"ryo",	"gya",	"gyu",	"gyo",	"bya",	"byu",	"byo",
				"pya",	"pyu",	"pyo",	"shi",	"chi",	"tsu",
				"ya",	"yu",	"yo",	"ka",	"ki",	"ku",	"ke",	"ko",	"sa",
				"su",	"se",	"so",	"ta",	"te",	"to",	"na",	"ni",	"nu",
				"ne",	"no",	"ha",	"hi",	"fu",	"he",	"ho",	"ma",	"mi",
				"mu",	"me",	"mo",	"ya",	"yu",	"yo",	"ra",	"ri",	"ru",
				"re",	"ro",	"wa",	"wi",	"we",	"wo",	"ga",	"gi",	"gu",
				"ge",	"go",	"za",	"ji",	"zu",	"ze",	"zo",	"ja",	"ju",
				"jo",	"da",	"di",	"du",	"de",	"do",	"ba",	"bi",	"bu",
				"be",	"bo",	"pa",	"pi",	"pu",	"pe",	"po",
				"a",	"i",	"u",	"e",	"o",	"n",	"b",	"c",	"d",
				"k",	"p",	"r",	"s",	"t",	"z"
			},
			
			hiragana = {
				"あ",	"い",	"う",	"え",	"お",	"ゃ",	"ゅ",	"ょ",
				"か",	"き",	"く",	"け",	"こ",	"きゃ",	"きゅ",	"きょ",
				"さ",	"し",	"す",	"せ",	"そ",	"しゃ",	"しゅ",	"しょ",
				"た",	"ち",	"つ",	"て",	"と",	"ちゃ",	"ちゅ",	"ちょ",
				"な",	"に",	"ぬ",	"ね",	"の",	"にゃ",	"にゅ",	"にょ",
				"は",	"ひ",	"ふ",	"へ",	"ほ",	"ひゃ",	"ひゅ",	"ひょ",
				"ま",	"み",	"む",	"め",	"も",	"みゃ",	"みゅ",	"みょ",
				"や",			"ゆ",			"よ",
				"ら",	"り",	"る",	"れ",	"ろ",	"りゃ",	"りゅ",	"りょ",
				"わ",	"ゐ",			"ゑ",	"を",
				"ん",
				"が",	"ぎ",	"ぐ",	"げ",	"ご",	"ぎゃ",	"ぎゅ",	"ぎょ",
				"ざ",	"じ",	"ず",	"ぜ",	"ぞ",	"じゃ",	"じゅ",	"じょ",
				"だ",	"ぢ",	"づ",	"で",	"ど",
				"ば",	"び",	"ぶ",	"べ",	"ぼ",	"びゃ",	"びゅ",	"びょ",
				"ぱ",	"ぴ",	"ぷ",	"ぺ",	"ぽ",	"ぴゃ",	"ぴゅ",	"ぴょ",
				"っ",	"っ",	"っ",	"っ",	"っ",	"っ",	"っ",	"っ",
				"っ"
			},
			
			katakana = {
				"ア",	"イ",	"ウ",	"エ",	"オ",	"ャ",	"ュ",	"ョ",
				"カ",	"キ",	"ク",	"ケ",	"コ",	"キャ",	"キュ",	"キョ",
				"サ",	"シ",	"ス",	"セ",	"ソ",	"シャ",	"シュ",	"ショ",
				"タ",	"チ",	"ッ",	"テ",	"ト",	"チャ",	"チュ",	"チョ",
				"ナ",	"ニ",	"ヌ",	"ネ",	"ノ",	"ニャ",	"ニュ",	"ニョ",
				"ハ",	"ヒ",	"フ",	"ヘ",	"ホ",	"ヒャ",	"ヒュ",	"ヒョ",
				"マ",	"ミ",	"ム",	"メ",	"モ",	"ミャ",	"ミュ",	"ミョ",
				"ヤ",			"ユ",			"ヨ",
				"ラ",	"リ",	"ル",	"レ",	"ロ",	"リャ",	"リュ",	"リョ",
				"ワ",	"ヰ",			"ヱ",	"ヲ",
				"ン",
				"ガ",	"ギ",	"グ",	"ゲ",	"ゴ",	"ギャ",	"ギュ",	"ギョ",
				"ザ",	"ジ",	"ズ",	"ゼ",	"ゾ",	"ジャ",	"ジュ",	"ジョ",
				"ダ",	"ヂ",	"ヅ",	"デ",	"ド",
				"バ",	"ビ",	"ブ",	"ベ",	"ボ",	"ビャ",	"ビュ",	"ビョ",
				"パ",	"ピ",	"プ",	"ペ",	"ポ",	"ピャ",	"ピュ",	"ピョ",
				"ッ",	"ッ",	"ッ",	"ッ",	"ッ",	"ッ",	"ッ",	"ッ",
				"ッ"
			},
			
			char_upper = {
				"A",	"B",	"C",	"D",	"E",	"F",	"G",	"H",	"I",
				"J",	"K",	"L",	"M",	"N",	"Ñ",	"O",	"P",	"Q",
				"R",	"S",	"T",	"U",	"V",	"W",	"X",	"Y",	"Z"
			}, --string.char(R(97, 122))
			
			char_lower = {
				"a",	"b",	"c",	"d",	"e",	"f",	"g",	"h",	"i",
				"j",	"k",	"l",	"m",	"n",	"ñ",	"o",	"p",	"q",
				"r",	"s",	"t",	"u",	"v",	"w",	"x",	"y",	"z"
			}, --string.char(R(65, 90))
			
			char_number = {
				"1", "2", "3", "4", "5", "6", "7", "8", "9", "0"
			}, --string.char(R(48, 57))
			
			char_special = {
				"°",	"¬",	"¡",	"!",	"¿",	"?",	"(",	")",	"[",
				"]",	"^",	"'",	"-",	"#",	"$",	"%",	"&",	";",
				":",	",",	".",	"<",	">",	"*",	"~",	"´",	"`",
				"¨",	"+",	"/",	"{",	"}",	"|",	"_",	"\\",	"\""
			},
			
			keeptags = {
				[01] = "\\bord%-?%d[%.%d]*",	[02] = "\\xbord%-?%d[%.%d]*",	[03] = "\\ybord%-?%d[%.%d]*",
				[04] = "\\shad%-?%d[%.%d]*",	[05] = "\\xshad%-?%d[%.%d]*",	[06] = "\\yshad%-?%d[%.%d]*",
				[07] = "\\blur%-?%d[%.%d]*",	[08] = "\\be%-?%d[%.%d]*",		[09] = "\\3c[%d&]^*[%.%d&H%x]*",
				[10] = "\\fscx%-?%d[%.%d]*",	[11] = "\\fscy%-?%d[%.%d]*",	[12] = "\\alpha[%d&]^*[%.%d&H%x]*",
				[13] = "\\fax%-?%d[%.%d]*",		[14] = "\\fay%-?%d[%.%d]*",		[15] = "\\1a[%d&]^*[%.%d&H%x]*",
				[16] = "\\frx%-?%d[%.%d]*",		[17] = "\\fry%-?%d[%.%d]*",		[18] = "\\3a[%d&]^*[%.%d&H%x]*",
				[19] = "\\fsp%-?%d[%.%d]*",		[20] = "\\fs%-?%d[%.%d]*",		[21] = "\\4a[%d&]^*[%.%d&H%x]*",
				[22] = "\\clip%b()",			[23] = "\\iclip%b()",			[24] = "\\[1]*c[%d&]^*[%.%d&H%x]*",
				[25] = "\\fad%b()",				[26] = "\\fr[z]*%-?%d[%.%d]*",	[27] = "\\4c[%d&]^*[%.%d&H%x]*",
			},
			
			remove = function(text, mode)
				local options = {
					["tags"] = function(text)
						--remove all tags from the entered text
						text = text:gsub("%b{}", "")
						return text
					end,
					
					["extra_space"] = function(text)
						--remove any blank spaces at the beginning and/or end of the text
						while text:sub(1, 1) == " " or text:sub(1, 1) == "	" do
							text = text:sub(2, -1)
						end
						while text:sub(-1, -1) == " " or text:sub(-1, -1) == "	" do
							text = text:sub(1, -2)
						end
						return text
					end,
					
					["space_in_tags"] = function(text)
						--remove any blank spaces within the tags
						text = text:gsub("%b{}",
							function(tags)
								local tags = tags:gsub("m%s+%-?%d[%.%-%d mlb]*",
									function(shp)
										local shp = shp:gsub(" ", "€")
										return shp
									end
								):gsub(" ", ""):gsub("€", " ")
								return tags
							end
						)
						return text
					end
				}
				return options[mode] and options[mode](text) or text
			end,
			
			to_upper = function(text)
				--converts text to uppercase without affecting tags
				text = text or "ke.text.to_upper"
				local tag_text, k = ke.string.array(text, "%b{}"), ke.math.count()
				text = text:gsub("%b{}", "@")
				text = unicode.to_upper_case(text):gsub("@", function(cap) return tag_text[k()] end)
				return text
			end, --ke.text.to_upper(fx.text)
			
			to_lower = function(text)
				--converts text to lowercase without affecting tags
				text = text or "ke.text.to_lower"
				local tag_text, k = ke.string.array(text, "%b{}"), ke.math.count()
				text = text:gsub("%b{}", "@")
				text = unicode.to_lower_case(text):gsub("@", function(cap) return tag_text[k()] end)
				return text
			end, --ke.text.to_lower(fx.text)
			
			to_kara = function(text, kmode)
				--converts the text, from romaji style, to syllabic karaoke
				local kmode, num = kmode or "k", 0
				kmode = not ke.table.inside({"k", "kf", "ko", "K"}, kmode) and "k" or kmode
				local words, times = ke.config.text2word(ke.text.to_lower(ke.text.remove(text, "tags")))
				for i, w in ipairs(words) do
					for _, rom in ipairs(ke.text.romaji) do
						w = w:gsub("[\128-\255]*" .. rom, "[%1]")
					end
					w, num = w:gsub("%b[]", "%1")
					words[i] = w:gsub("%b[]",
						function(capture)
							return ("{\\%s%d}%s"):format(kmode, times[i] / (num * 10), capture:gsub("%[", ""):gsub("%]", ""))
						end
					)
				end
				return table.concat(words)
			end, --ke.text.to_kara("inochi aru subete no mono yo")
			
			to_parts = function(text, duration, parts)
				--returns a table with the n-sized parts of a text
				local style = ke.infofx.data.l.style
				local fx = ke.infofx.data.fx
				local function _width(str)
					local txt_width = aegisub.text_extents(style, str)
					return txt_width
				end
				text, duration = text or fx.text, duration or fx.time_dur
				local durs, parts, left_spc = {}, parts or 2
				local parts_in_text = ke.string.parts(text, parts)
				local widths, lefts = {[0] = 0}, {[0] = fx.left}
				local char_dur = ke.math.round(duration / unicode.len(text), ROUND_NUM)
				for i = 1, #parts_in_text do
					left_spc = ""
					durs[i] = unicode.len(parts_in_text[i]) * char_dur
					while parts_in_text[i]:sub(1, 1) == " " or parts_in_text[i]:sub(1, 1) == "	" do
						left_spc = left_spc .. parts_in_text[i]:sub(1, 1)
						parts_in_text[i] = parts_in_text[i]:sub(2, -1)
					end
					widths[i] = _width(parts_in_text[i])
					lefts[i] = ke.math.round(lefts[i - 1] + widths[i - 1] + _width(left_spc), ROUND_NUM)
				end
				local rights, centers = {}, {}
				for i = 1, #parts_in_text do
					while parts_in_text[i]:sub(-1, -1) == " " or parts_in_text[i]:sub(-1, -1) == "	" do
						parts_in_text[i] = parts_in_text[i]:sub(1, -2)
					end
					widths[i]  = ke.math.round(_width(parts_in_text[i]), ROUND_NUM)
					rights[i]  = ke.math.round(lefts[i] + widths[i], ROUND_NUM)
					centers[i] = ke.math.round(lefts[i] + widths[i] / 2, ROUND_NUM)
				end --ke.text.to_parts(nil, nil, 5)
				widths[0], lefts[0] = nil, nil
				return parts_in_text, durs, centers, widths, lefts, rights
			end, --local p_txt, p_dur, p_cen, p_wid, p_lef, p_rig
			
			syl2hiragana = function(text)
				--converts the text from romaji to hiragana
				local roma_idx = ke.table.index(ke.text.romaji, text:lower():match("%w+"))
				local kata_idx = ke.table.index(ke.text.katakana, text:match("[\128-\255]+"))
				return roma_idx and text:lower():gsub(ke.text.romaji[roma_idx], ke.text.hiragana[roma_idx])
				or (kata_idx and text:gsub(ke.text.katakana[kata_idx], ke.text.hiragana[kata_idx])) or text
			end, --ke.text.syl2hiragana(syl.text)
			
			syl2katakana = function(text)
				--converts the text from romaji to katakana
				local roma_idx = ke.table.index(ke.text.romaji, text:lower():match("%w+"))
				local hira_idx = ke.table.index(ke.text.hiragana, text:match("[\128-\255]+"))
				return roma_idx and text:lower():gsub(ke.text.romaji[roma_idx], ke.text.hiragana[roma_idx])
				or (hira_idx and text:gsub(ke.text.katakana[hira_idx], ke.text.hiragana[hira_idx])) or text
			end, --ke.text.syl2katakana(syl.text)
			
			kana2romaji = function(text)
				--converts the text from kana (hiragana or katakana) to romaji
				local hira_idx = ke.table.index(ke.text.hiragana, text:match("[\128-\255]+"))
				local kata_idx = ke.table.index(ke.text.katakana, text:match("[\128-\255]+"))
				return hira_idx and text:lower():gsub(ke.text.romaji[hira_idx], ke.text.hiragana[hira_idx])
				or (kata_idx and text:gsub(ke.text.katakana[kata_idx], ke.text.hiragana[kata_idx])) or text
			end,
			
			char2byte = function(text)
				--returns a table with the byte (number) of each character in the text
				local bytes, c = {}
				for c in unicode.chars(text) do
					bytes[#bytes + 1] = c:byte()
				end
				return bytes
			end,
			
			byte2char = function(Bytes)
				--converts a byte table into the corresponding string
				return string.char(table.unpack(Bytes))
			end,
			
			tag = function(text, ...)
				local tags = type(...) == "table" and ... or {...}
				local texttag, text = "", text or "no text"
				local chars = ke.string.array(text, "chars")
				local ipols, n = ke.table.new(#chars, ""), #chars
				local str2tbl = function(str)
					local tag, val = str:match("(\\%w+)(%b{})")
					val = val:gsub("&H%x+&", "\"%1\"")
					val = ke.string.toval(val)
					return type(val) == "table" and val:filter(function(k, v) return ("%s%s"):format(tag, v) end) or nil
				end
				for i = 1, n do
					for k, tag in ipairs(tags) do
						local xval = str2tbl(tag)
						ipols[i] = xval and ipols[i] .. ke.tag.ipol(xval, (i - 1) / (n - 1)) or ""
					end
					texttag = texttag .. (chars[i] == " " and " " or ("{%s}%s"):format(ipols[i], chars[i]))
				end
				return texttag
			end, --ke.text.tag(fx.text, "\\fscy{100, 200, 50, 120}", "\\1c{&H00FFFF&, &HFF00FF&, &HFFFF00&}")
			
			rand = function(text, num_tran, dur_tran, tags, extra, mode, all)
				local fx = ke.infofx.data.fx
				local frame_dur = ke.infofx.data.frame_dur
				local text = text or fx.text
				local dur_tran = math.abs(dur_tran or 2 * frame_dur)
				local num_tran = math.abs(ke.math.round(num_tran or 5))
				local delay_tr = dur_tran * num_tran
				local del_tran, table_ch = 0, {}
				dur_tran = dur_tran < frame_dur and frame_dur or dur_tran
				if delay_tr == 0 or delay_tr > fx.time_dur then
					delay_tr = fx.time_dur
					num_tran = math.ceil(fx.time_dur / dur_tran)
				end
				for i = 48, 57 do --dígitos
					table_ch[#table_ch + 1] = string.char(i)
				end
				for i = 65, 90 do --minúsculas y mayúsculas
					table_ch[#table_ch + 1] = string.char(i)
					table_ch[#table_ch + 1] = string.char(i + 32)
				end
				local tbl_rand, extra_tg = extra or table_ch, tags or ""
				local time_ini = ke.math.rand(0, fx.time_dur - delay_tr, 5 * frame_dur)
				time_ini = (mode == "intro" or mode == "line") and 0 or (mode == "outro" and fx.time_dur - delay_tr) or time_ini
				local tbl_char, tbl_rtrn = ke.string.array(text, "chars"), {}
				local time_line = fx.time_dur - delay_tr
				local l = ke.infofx.data.l
				local Ad = (l.outline == 0 and l.shadow == 0) and ("\\1a%s"):format(l.alpha1)
				or (l.shadow == 0 and ("\\1a%s\\3a%s"):format(l.alpha1, l.alpha3))
				or (l.outline == 0 and ("\\1a%s\\4a%s"):format(l.alpha1, l.alpha4))
				or format("\\1a%s\\3a%s\\4a%s", l.alpha1, l.alpha3, l.alpha4)
				local Ai = (l.outline == 0 and l.shadow == 0) and "\\1a&HFF&" or (l.shadow == 0 and "\\1a&HFF&\\3a&HFF&")
				or (l.outline == 0 and "\\1a&HFF&\\4a&HFF&") or "\\1a&HFF&\\3a&HFF&\\4a&HFF&"
				for i = 1, #tbl_char do
					if tbl_char[i] ~= " " then
						if ke.table.inside(ke.text.char_special, tbl_char[i]) then
							tbl_rtrn[i] = ("{\\fscx%s}%s"):format(l.scale_x, tbl_char[i])
						else
							if mode == "line" then
								tbl_rtrn[i] = ("{%s\\fscx%s%s\\t(%s,%s,\\fscx0%s)\\t(%s,%s,\\fscx%s%s)\\t(%s,%s,\\fscx0%s)}%s"):format(
									ke.tag.default(extra_tg),
									l.scale_x, Ad, time_ini, time_ini + del_tran, Ai, time_ini + delay_tr, time_ini + delay_tr + del_tran,
									l.scale_x, Ad, time_line, time_line + del_tran, Ai, tbl_char[i]
								)
								for k = 1, num_tran do
									tbl_rtrn[i] = tbl_rtrn[i] .. ("{\\fscx0%s\\t(%s,%s,\\fscx%s%s%s)\\t(%s,%s,\\fscx0%s%s)\\t(%s,%s,\\fscx%s%s)\\t(%s,%s,\\fscx0%s)}%s"):format(
										Ai, time_ini + (k - 1) * dur_tran, time_ini + del_tran + (k - 1) * dur_tran, l.scale_x, Ad, extra_tg,
										time_ini + (k - 0) * dur_tran, time_ini + del_tran + (k - 0) * dur_tran, Ai, ke.tag.default(extra_tg),
										time_line + (k - 1) * dur_tran, time_line + del_tran + (k - 1) * dur_tran, l.scale_x, Ad,
										time_line + (k - 0) * dur_tran, time_line + del_tran + (k - 0) * dur_tran, Ai, ke.math.rand(tbl_rand)
									)
								end
							else
								tbl_rtrn[i] = ("{%s\\fscx%s%s\\t(%s,%s,\\fscx0%s)\\t(%s,%s,\\fscx%s%s)}%s"):format(
									ke.tag.default(extra_tg),
									l.scale_x, Ad, time_ini, time_ini + del_tran, Ai, time_ini + delay_tr,
									time_ini + delay_tr + del_tran, l.scale_x, Ad, tbl_char[i]
								)
								for k = 1, num_tran do
									tbl_rtrn[i] = tbl_rtrn[i] .. ("{\\fscx0%s\\t(%s,%s,\\fscx%s%s%s)\\t(%s,%s,\\fscx0%s%s)}%s"):format(
										Ai, time_ini + (k - 1) * dur_tran, time_ini + del_tran + (k - 1) * dur_tran, l.scale_x, Ad, extra_tg,
										time_ini + k * dur_tran, time_ini + del_tran + k * dur_tran, Ai, ke.tag.default(extra_tg), ke.math.rand(tbl_rand)
									)
								end
							end
						end
					end
				end
				local Text_fx = ke.tag.dark(table.concat(tbl_rtrn))
				Text_fx = Text_fx:gsub("\\t(%b())",
					function(capture)
						if capture:sub(2, -2):sub(1, 4) == "0,0," then
							return capture:sub(2, -2):match("\\%S+[%S]*")
						end --captura todos los tags dentro de una \\t
					end
				) --si hay una \\t(0,0, solo retorna los tags que hay dentro
				if all or mode == "intro" or mode == "line" or mode == "outro" then
					return Text_fx --table.concat(tbl_rtrn)
				end --char.text:rand(5, 2f, "\\1cR()")
				return ke.tag.only(ke.math.rand(ke.math.rand(2, 4)) == 1, Text_fx, text)
			end, --ke.text.rand(fx.text, 5, 82)
			
			move = function(text, dx, dy, Ox, Oy, accel)
				local fx = ke.infofx.data.fx
				local text = text or fx.text
				local function count_space_end(str)
					local space, i = 0, 1
					while str:sub(-i, -i) == " " do
						space = space + 1
						i = i + 1
					end
					return space
				end
				fx.add_tags = fx.add_tags:gsub("\\\\", "\\")
				local Off_x = Ox or 0 --\\fsp
				local Off_y = Oy or 0 --\\fscy
				local Ini_x = aegisub.text_extents(ke.infofx.data.l.style, ".")
				local tagsi = ("{\\p0}\\N{\\r%s\\p1}%s"):format(fx.add_tags, text)
				local tagsa = "\\p0\\r\\alpha&HFF&"
				if ke.table.type({text}) ~= "shape" then
					Ini_x = aegisub.text_extents(ke.infofx.data.l.style, ".") + count_space_end(text) * aegisub.text_extents(ke.infofx.data.l.style, " ")
					tagsi = ("{\\p0}\\N{\\r%s\\q2}%s"):format(fx.add_tags, text)
					tagsa = "\\r\\alpha&HFF&"
				end --ke.table.type({ke.shape.circle})
				local tagsx, tagsy = dx or "", dy or ""
				fx.add_tags = "" -->no se está borrando en realidad
				Off_y = 2 * Off_y --los valores en "y" deben duplicarse
				tagsx = type(tagsx) == "number" and ("\\t(%s,%s,\\fsp%s)"):format(fx.t1, fx.t2, tagsx) or tagsx
				tagsy = type(tagsy) == "number" and ("\\t(%s,%s,\\fscy%s)"):format(fx.t1, fx.t2, tagsy) or tagsy
				local Mov_x = ("%s\\fsp%s"):format(tagsa, -Ini_x - 2 * Off_x)
				if type(tagsx) == "table" then
					local transfo_cap_x = ke.table.match(tagsx, "\\t%(")
					if #transfo_cap_x > 0 then
						tagsx = table.concat(tagsx)
					elseif ke.table.type(tagsx) == "number" then
						Mov_x = ("%s\\fsp%s"):format(tagsa, -Ini_x - 2 * tagsx[1])
						if #tagsx > 1 then
							local dur = fx.time_dur / (#tagsx - 1)
							for i = 2, #tagsx do
								Mov_x = Mov_x .. ("\\t(%s,%s,\\fsp%s)"):format((i - 2) * dur, (i - 1) * dur, -Ini_x - 2 * tagsx[i])
							end
						end
						tagsx = ""
					elseif ke.table.type(tagsx) == "table" then
						Mov_x = ("%s\\fsp%s"):format(tagsa, -Ini_x - 2 * tagsx[1][1])
						if #tagsx[1] > 1 then
							for i = 2, #tagsx[1] do
							--	Mov_x = Mov_x .. ("\\t(%s,%s,\\fsp%s)"):format(tagsx[2][i - 1], tagsx[2][i], -Ini_x - 2 * tagsx[1][i])
								Mov_x = Mov_x .. ("\\t(%s,%s,\\fsp%s)"):format(tagsx[2][i - 1], tagsx[2][i], -Ini_x - 2 * tagsx[1][i])
							end
						end
						tagsx = ""
					end
				else
					tagsx = tagsx:gsub("\\fsp(%-?%d[%.%d]*)", function(val) return "\\fsp" .. -Ini_x - 2 * tonumber(val) end)
					:gsub("\\fsp(R[%a]*%b())", function(val) return "\\fsp" .. -Ini_x - 2 * ke.string.toval(val) end)
					:gsub("\\fsp(%b())", function(val) return "\\fsp" .. -Ini_x - 2 * ke.string.toval(val) end)
				end
				local Mov_H = ("{%s%s}."):format(Mov_x, tagsx)
				------------------------------------------------------------------
				local Mov_y1 = ("\\r\\fscy%s"):format((Off_y >= 0) and Off_y or 0)
				tagsy = type(tagsy) == "table" and table.concat(tagsy) or tagsy
				tagsy = tagsy:gsub("\\fscy(R[%a]*%b())", function(val) return "\\fscy" .. ke.string.toval(val) end)
				:gsub("\\fscy(%b())", function(val) return "\\fscy" .. ke.string.toval(val) end)
				:gsub("\\fscy(%-?%d[%.%d]*)", function(val) return "\\fscy" .. 2 * tonumber(val) end)
				local valsy, t = {[0] = Off_y}
				for t in tagsy:gmatch("\\t%b()") do
					valsy[#valsy + 1] = tonumber(t:match("\\fscy(%-?%d[%.%d]*)"))
				end
				local k, transfo = 1, {p = {}, n = {}}
				local t1, t2, vy, dy
				for t in tagsy:gmatch("\\t%b()") do
					t1 = tonumber(t:match("\\t%((%d[%.%d]*),%d[%.%d]*,"))
					t2 = tonumber(t:match("\\t%(%d[%.%d]*,(%d[%.%d]*),"))
					vy = tonumber(t:match("\\fscy(%-?%d[%.%d]*)"))
					if vy < 0 then
						if vy * valsy[k - 1] >= 0 then
							transfo.n[#transfo.n + 1] = t:gsub("(\\fscy)%-(%d[%.%d]*)", "%1%2")
						else
							dy = valsy[k - 1] - vy
							transfo.p[#transfo.p + 1] = ("\\t(%s,%s,\\fscy0)"):format(t1, t1 - (t2 - t1) * vy / dy)
							transfo.n[#transfo.n + 1] = ("\\t(%s,%s,\\fscy%s)"):format(t1 - (t2 - t1) * vy / dy, t2, -vy)
						end
					else
						if vy * valsy[k - 1] >= 0 then
							transfo.p[#transfo.p + 1] = t
						else
							dy = vy - valsy[k - 1]
							transfo.n[#transfo.n + 1] = ("\\t(%s,%s,\\fscy0)"):format(t1, t1 + (t2 - t1) * vy / dy)
							transfo.p[#transfo.p + 1] = ("\\t(%s,%s,\\fscy%s)"):format(t1 + (t2 - t1) * vy / dy, t2, vy)
						end
					end
					k = k + 1
				end
				local Mov_V1 = ("{%s%s\\p1}m 0 0 m 0 100 "):format(Mov_y1, table.concat(transfo.p))
				local Mov_y2 = ("\\r\\fscy%s"):format((Off_y <= 0) and ((Off_y == 0) and 0 or -Off_y) or 0)
				local Mov_V2 = ("\\N{%s%s\\p1}m 0 0 m 0 100 "):format(Mov_y2, table.concat(transfo.n))
				return Mov_V1 .. tagsi .. Mov_H .. Mov_V2
			end, --ke.text.move(nil, ke.tag.oscill(fx.time_dur, 5f, "\\fspR(10)"), ke.tag.oscill(fx.time_dur, 5f, "\\fscyR(10)"))
			
		},
		
		tag = {
			
			list = {
				animated = {
					[01] = "\\1c",		[02] = "\\2c",		[03] = "\\3c",		[04] = "\\4c",		[05] = "\\c",
					[06] = "\\1a",		[07] = "\\2a",		[08] = "\\3a",		[09] = "\\4a",		[10] = "\\alpha",
					[11] = "\\fsp",		[12] = "\\xbord",	[13] = "\\ybord",	[14] = "\\bord",	[15] = "\\xshad",
					[16] = "\\yshad",	[17] = "\\shad",	[18] = "\\fscx",	[19] = "\\fscy",	[20] = "\\fs",
					[21] = "\\frx",		[22] = "\\fry",		[23] = "\\frz",		[24] = "\\fr",		[25] = "\\blur",
					[26] = "\\be",		[27] = "\\fax",		[28] = "\\fay",		[29] = "\\clip",	[30] = "\\iclip",
				},
				
				unanimated = {
					[01] = "\\n",		[02] = "\\N",		[03] = "\\h",		[04] = "\\q",		[05] = "\\a",
					[06] = "\\an",		[07] = "\\i",		[08] = "\\b",		[09] = "\\u",		[10] = "\\s",
					[11] = "\\fn",		[12] = "\\fe",		[13] = "\\k",		[14] = "\\K",		[15] = "\\kf",
					[16] = "\\ko",		[17] = "\\r",		[18] = "\\p",		[19] = "\\pos",		[20] = "\\move",
					[21] = "\\org",		[22] = "\\fad",		[23] = "\\fade",	[24] = "\\t",
				},
				
				functions = {
					[01] = "\\pos",		[02] = "\\move",	[03] = "\\org",		[04] = "\\fad",		[05] = "\\fade",
					[06] = "\\clip",	[07] = "\\iclip",	[08] = "\\t",
				},
				
				dark = {
					["in"] = {
						[01] = "\\fscxy",	[02] = "\\faxy",	[03] = "\\frxyz",	[04] = "\\frxy",	[05] = "\\frxz",
						[06] = "\\fryz",	[07] = "\\xybord",	[08] = "\\xyshad",	[09] = "\\bs",		[10] = "\\13a",
						[11] = "\\14a",		[12] = "\\34a",		[13] = "\\134a",	[14] = "\\13c",		[15] = "\\14c",
						[16] = "\\34c",		[17] = "\\134c",
					},
					["out"] = {
						[01] = "\\fscx%s\\fscy%s",		[02] = "\\fax%s\\fay%s",		[03] = "\\frx%s\\fry%s\\frz%s",
						[04] = "\\frx%s\\fry%s",		[05] = "\\frx%s\\frz%s",		[06] = "\\fry%s\\frz%s",
						[07] = "\\xbord%s\\ybord%s",	[08] = "\\xshad%s\\yshad%s",	[09] = "\\bord%s\\shad%s",
						[10] = "\\1a%s\\3a%s",			[11] = "\\1a%s\\4a%s",			[12] = "\\3a%s\\4a%s",
						[13] = "\\1a%s\\3a%s\\4a%s",	[14] = "\\1c%s\\3c%s",			[15] = "\\1c%s\\4c%s",
						[16] = "\\3c%s\\4c%s",			[17] = "\\1c%s\\3c%s\\4c%s",
					}
				}
			},
			
			tonumber = function(str)
				str = type(str) == "function" and str() or str or ""
				str = str:gsub("(%-?%d[%.%d]*)([fr]^*)",
					function(capture, variable)
						local varx = variable == "f" and frame_dur or ratio
						return tonumber(capture) * varx
					end
				)
				return str
			end, --ke.tag.tonumber("\\alpha45\\foo5f\\bar2r\\3a255")
			
			default = function(str)
				local l = ke.infofx.data.l
				local result, str = "", str or ""
				local tags, array = ke.tag.list.animated, {}
				local vals = {
					[01] = "\\1c" .. l.color1,		[02] = "\\2c" .. l.color2,		[03] = "\\3c" .. l.color3,
					[04] = "\\4c" .. l.color4,		[05] = "\\1c" .. l.color1,		[06] = "\\1a" .. l.alpha1,
					[07] = "\\2a" .. l.alpha2,		[08] = "\\3a" .. l.alpha3,		[09] = "\\4a" .. l.alpha4,
					[10] = "\\alpha&H00&",			[11] = "\\fsp" .. l.spacing,	[12] = "\\xbord" .. l.outline,
					[13] = "\\ybord" .. l.outline,	[14] = "\\bord" .. l.outline,	[15] = "\\xshad" .. l.shadow,
					[16] = "\\yshad" .. l.shadow,	[17] = "\\shad" .. l.shadow,	[18] = "\\fscx" .. l.scale_x,
					[19] = "\\fscy" .. l.scale_y,	[20] = "\\fs" .. l.fontsize,	[21] = "\\frx0",
					[22] = "\\fry0",				[23] = "\\frz" .. l.angle,		[24] = "\\fr" .. l.angle,
					[25] = "\\blur0",				[26] = "\\be0",					[27] = "\\fax0",
					[28] = "\\fay0",				[29] = "",						[30] = "",
				}
				local tval = {"%-?[%d&]^*[%.%dH%x&]*", "%b()"}
				for i, tg in ipairs(tags) do
					for _, v in ipairs(tval) do
						str = str:gsub(tg .. v, function(tag) return "@" .. vals[i] .. "@" end)
					end
				end
				str = str:gsub("%b@@", function(cap) array[#array + 1] = cap:sub(2, -2) end)
				array = ke.table.get(array, "unique", "last")
				result = #array > 0 and table.concat(array) or result
				return result
			end, --ke.tag.default("\\fscx250\\t(0,300,\\1a&HFF&)")
			
			inverse = function(str)
				local l = ke.infofx.data.l
				local result, str = "", str or ""
				local tags, array = ke.tag.list.animated, {}
				local tval = {"%-?[%d&]^*[%.%dH%x&]*", "%b()"}
				for i, tg in ipairs(tags) do
					for _, v in ipairs(tval) do
						local pattern = ("(%s)(%s)"):format(tg, v)
						str = str:gsub(pattern,
							function(tag, val)
								val = ke.string.toval(val)
								local invtag
								if type(val) == "string" and val:match("&H%x+&") then
									if val:match("&H%x%x%x%x%x%x&") then
										local b, g, r = val:match("(%x%x)(%x%x)(%x%x)")
										b, g, r = 255 - tonumber(b, 16), 255 - tonumber(g, 16), 255 - tonumber(r, 16)
										invtag = tag .. ke.color.ass(r, g, b)
									else
										invtag = tag .. ("&H%X&"):format(255 - tonumber(val:match("%x%x"), 16))
									end
								elseif tag:match("\\be?[lur]*") or tag:match("\\[xy]*bord") then
									invtag = tag .. "0"
								elseif tag:match("\\fsc[xy]^*") then
									invtag = tag .. (tag:match("x") and l.scale_x or l.scale_y)
								elseif tag:match("\\fs") or tag:match("\\shad") then
									invtag = tag .. val
								elseif type(val) == "number" then
									invtag = tag .. ("%s"):format(-1 * val)
								end
								return invtag and "@" .. invtag .. "@" or ""
							end
						)
					end
				end
				str = str:gsub("%b@@", function(cap) array[#array + 1] = cap:sub(2, -2) end)
				array = ke.table.get(array, "unique", "last")
				result = #array > 0 and table.concat(array) or result
				return result
			end, --ke.tag.inverse("\\fscx250\\t(0,300,\\1a&HAA&\\frz45)")
			
			times = function(str) --\\t%b()
				local function retimettag(mode, t1, t2)
					local times, fx = ke.infofx.data.times, ke.infofx.data.fx
					local ini = times.line.start_time - fx.time_ini
					local fin = times.line.end_time - fx.time_ini
					local modes = {
						["line"] = {ini, fin},
						["preline"] = {ini, ini},
						["postline"] = {fin, fin},
						["word"] = {ini + times.word.start_time, ini + times.word.end_time},
						["preword"] = {ini + times.word.start_time, ini + times.word.start_time},
						["postword"] = {ini + times.word.end_time, ini + times.word.end_time},
						["syl"] = {ini + times.syl.start_time, ini + times.syl.end_time},
						["presyl"] = {ini + times.syl.start_time, ini + times.syl.start_time},
						["postsyl"] = {ini + times.syl.end_time, ini + times.syl.end_time},
						["char"] = {ini + times.char.start_time, ini + times.char.end_time},
						["prechar"] = {ini + times.char.start_time, ini + times.char.start_time},
						["postchar"] = {ini + times.char.end_time, ini + times.char.end_time},
						["start2word"] = {ini, times.line.start_time + times.word.start_time - fx.time_ini},
						["word2end"] = {ini + times.word.end_time, fin},
						["start2syl"] = {ini, times.line.start_time + times.syl.start_time - fx.time_ini},
						["syl2end"] = {ini + times.syl.end_time, fin},
						["start2char"] = {ini, times.line.start_time + times.char.start_time - fx.time_ini},
						["char2end"] = {ini + times.char.end_time, fin},
						["set"] = {-fx.time_ini, -fx.time_ini},
						["startsyl2char"] = {ini + times.syl.start_time, ini + times.char.start_time},
						["startword2syl"] = {ini + times.word.start_time, ini + times.syl.start_time},
						["startword2char"] = {ini + times.word.start_time, ini + times.char.start_time},
						["syl2endword"] = {ini + times.syl.end_time, ini + times.word.end_time},
						["char2endsyl"] = {ini + times.char.end_time, ini + times.syl.end_time},
						["char2endword"] = {ini + times.char.end_time, ini + times.word.end_time},
						["end"] = {fx.time_dur, fx.time_dur},
					}
					t1 = modes[mode] and modes[mode][1] + t1 or t1
					t2 = modes[mode] and modes[mode][2] + t2 or t2
					return t1, t2
				end
				local tmode
				local fx_dur = ke.infofx.data.fx.time_dur
				str = str:gsub("\\t%b()",
					function(ttag)
						tmode = ttag:match("\\t%(%s*(%l+%d)%s*,")
						if tmode and tmode:match("mode%d") then
							ttag = ttag:gsub("\\t%(%s*(%l+%d)%s*,", "\\t(")
							local t1, t2, acc = table.unpack(ke.tag.array(ttag)[1].times)
							local ttags = ke.tag.array(ttag)[1].tags
							local dtags = ke.tag.default(ttags)
							local itags = ke.tag.inverse(ttags)
							local dur = t2 - t1
							local modes = {
								--normal + inverso + normal --> \\t(0,0,\\xtags)\\t(0,0.5,\\itags)\\t(0.5,dur,xtags)
								[1] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(
									t1, t1, acc, ttags, t1, t1 + 0.5 * dur, acc, itags, t1 + 0.5 * dur, t1 + dur, acc, ttags
								), --"\\t(mode1,1000,2000,\\xshad-4\\fscxy150)"
								--normal + default + normal --> \\t(0,0,\\xtags)\\t(0,0.5,\\dtags)\\t(0.5,dur,xtags)
								[2] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(
									t1, t1, acc, ttags, t1, t1 + 0.5 * dur, acc, dtags, t1 + 0.5 * dur, t1 + dur, acc, ttags
								), --"\\t(mode2,1000,2000,\\xshad-4\\fscxy160)"
								--normal + inverso + default --> \\t(0,0,\\xtags)\\t(0,0.5,\\itags)\\t(0.5,dur,dtags)
								[3] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(
									t1, t1, acc, ttags, t1, t1 + 0.5 * dur, acc, itags, t1 + 0.5 * dur, t1 + dur, acc, dtags
								), --"\\t(mode3,\\frxyzR(20, 60))"
								--normal + inverso + default --> \\t(0,0.25,\\xtags)\\t(0.25,0.75,\\itags)\\t(0.75,dur,dtags)
								[4] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(
									t1, t1 + 0.25 * dur, acc, ttags, t1 + 0.25 * dur, t1 + 0.75 * dur, acc, itags, t1 + 0.75 * dur, t1 + dur, acc, dtags
								), --"\\t(mode4,\\xshad-10r\\1cR())"
								--normal + default --> \\t(0,0.5,\\xtags)\\t(0.5,dur,\\dtags)
								[5] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(
									t1, t1 + 0.5 * dur, acc, ttags, t1 + 0.5 * dur, t1 + dur, acc, dtags
								), --"\\t(mode5,0,320,\\fscxy145\\blur1.4)"
								--normal + inverse --> \\t(0,0.5,\\xtags)\\t(0.5,dur,\\itags)
								[6] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(
									t1, t1 + 0.5 * dur, acc, ttags, t1 + 0.5 * dur, t1 + dur, acc, itags
								), --"\\t(mode6,0,320,\\frxzR(60, 100))"
								--normal + defautl --> \\t(0,dur,\\xtags)\\t(dur,fx.dur,\\dtags)
								[7] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(t1, t2, acc, ttags, t2, fx_dur, acc, dtags), --"\\t(mode7,0,320,\\frxzR(60, 100))"
								--normal + inverse --> \\t(0,dur,\\xtags)\\t(dur,fx.dur,\\itags)
								[8] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(t1, t2, acc, ttags, t2, fx_dur, acc, itags), --"\\t(mode8,0,320,\\frxzR(60, 100))"
								--normal + default + normal --> \\t(0,0,\\xtags)\\t(0,dur,\\dtags)\\t(dur,fx.dur,\\xtags)
								[9] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(
									t1, t1, acc, ttags, t1, t2, acc, dtags, t2, fx_dur, acc, ttags
								), --"\\t(mode9,0,320,\\frxzR(60, 100))"
								--normal + default + inverse --> \\t(0,0,\\xtags)\\t(0,dur,\\dtags)\\t(dur,fx.dur,\\itags)
								[0] = ("\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)\\t(%s,%s,%s,%s)"):format(
									t1, t1, acc, ttags, t1, t2, acc, dtags, t2, fx_dur, acc, itags
								), --"\\t(mode0,0,320,\\frxzRs(60, 100))"
							}
							tmode = tonumber(tmode:match("mode(%d)"))
							return modes[tmode] or nil
						end --ke.tag.times("\\t(mode2,1000,2000,\\xshad-4\\fscxy150)")
					end
				)
				:gsub("\\t%b()",
					function(ttag)
						ttag = ttag:gsub("\\t%(%s*(%l+)%s*,", function(mode) tmode = mode return "\\t(" end)
						local t1, t2, acc = table.unpack(ke.tag.array(ttag)[1].times)
						acc = acc ~= 1 and acc .. "," or "" --delete acc = 1
						t1, t2 = retimettag(tmode, t1, t2)
						local tt = ("%s,%s,"):format(t1, t2)
						tt = (t1 == 0 and math.abs(fx_dur - t2) <= 1) and "" or tt --delete 0,fx.dur,
						ttag = ttag:gsub("\\t%((.-)\\",
							function(times)
								return ("\\t(%s%s\\"):format(tt, acc)
							end
						)
						return ttag
					end
				)
				return str
			end,
			
			dark = function(str)
				--return str
				---[[
				local fx, fx__ = ke.infofx.data.fx, ke.infofx.data.fx__
				local l = ke.infofx.data.l
				local tagdef1 = {
					["\\13cs~"] = "\\1cs~\\3cs~",	["\\14cs~"] = "\\1cs~\\4cs~",
					["\\34cs~"] = "\\3cs~\\4cs~",	["\\134cs~"] = "\\1cs~\\3cs~\\4cs~", 
					["\\13as~"] = "\\1as~\\3as~",	["\\14as~"] = "\\1as~\\4as~",
					["\\34as~"] = "\\3as~\\4as~",	["\\134as~"] = "\\1as~\\3as~\\4as~",
					["\\13c~"] = "\\1c~\\3c~",		["\\14c~"] = "\\1c~\\4c~",
					["\\34c~"] = "\\3c~\\4c~",		["\\134c~"] = "\\1c~\\3c~\\4c~",
					["\\13a~"] = "\\1a~\\3a~",		["\\14a~"] = "\\1a~\\4a~",
					["\\34a~"] = "\\3a~\\4a~",		["\\134a~"] = "\\1a~\\3a~\\4a~",
					["\\frxy~"] = "\\frx0\\fry0",	["\\xybord~"] = "\\xbord~\\ybord~",
					["\\frxz~"] = "\\frx0\\frz~",	["\\xyshad~"] = "\\xshad~\\yshad~",
					["\\fryz~"] = "\\fry0\\frz~",	["\\frxyz~"] = "\\frx0\\fry0\\frz~",
					["\\faxy~"] = "\\fax0\\fay0",	["\\fscxy~"] = "\\fscx~\\fscy~",
					["\\bs~"] = "\\bord~\\shadow~",
				}
				local tagdef2 = {
					["\\1c~"] = l.color1,		["\\2c~"] = l.color2,		["\\3c~"] = l.color3,
					["\\4c~"] = l.color4,		["\\c~"] = l.color1,		["\\1a~"] = l.alpha1,
					["\\2a~"] = l.alpha2,		["\\3a~"] = l.alpha3,		["\\4a~"] = l.alpha4,
					["\\alpha~"] = "&H00&",		["\\fsp~"] = l.spacing,		["\\xbord~"] = l.outline,
					["\\ybord~"] = l.outline,	["\\bord~"] = l.outline,	["\\xshad~"] = l.shadow,
					["\\yshad~"] = l.shadow,	["\\shad~"] = l.shadow,		["\\fscx~"] = l.scale_x,
					["\\fscy~"] = l.scale_y,	["\\fs~"] = l.fontsize,		["\\frx~"] = 0,
					["\\fry~"] = 0,				["\\frz~"] = l.angle,		["\\fr~"] = l.angle,
					["\\blur~"] = 0,			["\\be~"] = 0,				["\\fax~"] = 0,
					["\\fay~"] = 0,								["\\org~"] = ("(%s,%s)"):format(fx.x, fx.y),
					["\\1cs~"] = ke.color.ass(fx__.fx_color1),	["\\1as~"] = ke.alpha.ass(fx__.fx_alpha1),
					["\\3cs~"] = ke.color.ass(fx__.fx_color3),	["\\3as~"] = ke.alpha.ass(fx__.fx_alpha3),
					["\\4cs~"] = ke.color.ass(fx__.fx_color4),	["\\4as~"] = ke.alpha.ass(fx__.fx_alpha4)
				}
				local changes = {
					[1] = {{"(%-?%d[%.%d]*)([fjr]^*)"}, function(cap, var)
							local varx = var == "f" and frame_dur or ratio
							varx = var == "j" and ke.infofx.data.j or varx
							return tonumber(cap) * varx
						end
					},
					[2] = {tagdef1, function(cap) return tagdef1[cap] end},
					[3] = {tagdef2, function(cap) local v = tagdef2[cap] cap = cap:gsub("s?~", "") return cap .. v end},
					[4] = {{"(\\[%d]*%l+)R(%b())"}, function(tag, rand) --\\tagR()
							local randfunct = "ke.math.rand"
							randfunct = tag:match("\\%d+c") and "ke.color.random"
							or (tag:match("\\%d+a") and "ke.alpha.random" or randfunct)
							return ("%s(%s%s)"):format(tag, randfunct, rand)
						end
					},
					[5] = {ke.tag.list.dark["in"], function(tag, val) --tag.dark
							local k = ke.table.index(ke.tag.list.dark["in"], tag)
							return ke.tag.list.dark["out"][k]:format(val, val, val)
						end, {"(%b())", "([^\\}()]*)"}
					},
					[6] = {{"(\\%d*[^t]%l+)(%b())"}, function(tag, val) --tags function (without \\t)
							val = val:gsub("m%s+%-?%d[%.%-%d mlb]*", "'%1'"):gsub("center", "'%1'")
							val = "{" .. val:sub(2, -2) .. "}"
							val = ke.string.toval(val)
							val = type(val) == "table" and table.concat(val, ",") or val:gsub("{", ""):gsub("}", "")
							val = val:match(",") and "(" .. val .. ")" or val
							val = val:gsub("m%s+%-?%d[%.%-%d mlb]*", "(%1)")
							return ("%s%s"):format(tag, val)
						end
					},
					[7] = {{"\\t%b()"}, function(cap) --tags \\t
							local tmode = cap:match("\\t%(%s*(%l+%d*)%s*,") --get mode
							cap = cap:gsub("\\t%(%s*%l+%d*%s*,", "\\t(")	--delete mode
							local tset = ke.tag.array(cap)[1]
							if not tset.tags then
								return "" --delete empty \\t
							elseif (tset.times[1] == 0 and tset.times[2] == 0) and not tmode then
								return tset.tags or ""
							end --si hay una \\t(0,0, solo retorna los tags que hay dentro
							local mode = tmode and tmode .. "," or ""
							cap = ("\\t(%s%s,%s,%s,%s)"):format(mode, tset.times[1], tset.times[2], tset.times[3], tset.tags) --insert mode
							cap = ke.tag.times(cap)
							return cap
						end --"\\t(0,ke.math.rand(300,400),\\fscxyR(120,150))"
					},
					[8] = {{"(\\t%b())([%-%~]^*)"}, function(cap, sign) --\\t()- or \\t()~
							local tset = ke.tag.array(cap)[1]
							local ttags = tset.tags
							local xtags = sign == "~" and ke.tag.default(ttags) or ke.tag.inverse(ttags)
							local val = cap:match("\\t(%b())"):gsub("\\.+", "")
							return ("%s\\t%s%s)"):format(ttags, val, xtags)
						end --"\\t(0,ke.math.rand(300,400),\\fscxyR(120,150))~"
					},
					[9] = {{"(\\i?clip)(%b())"}, function(tag, val) --\\clip(shape)
							if val:match("m%s+%-?%d[%.%-%d mlb]*") and val:match(",") then
								local fx = ke.infofx.data.fx
								local shp = val:match("m%s+%-?%d[%.%-%d mlb]*")
								if val:match("center") then --"\\iclip(ke.shape.circle, center)"
									local dx, dy = val:match("center%s*,%s*(%-?%d[%.%d]*)%s*,%s*(%-?%d[%.%d]*)")
									dx, dy = dx and tonumber(dx) or 0, dy and tonumber(dy) or 0
									shp = ke.shape.displace(shp, {x = fx.x + dx, y = fx.y + dy, mode = "center"}).code
								elseif val:match(",%s*(%-?%d[%.%d]*)%s*,%s*(%-?%d[%.%d]*)") then
									local dx, dy = val:match(",%s*(%-?%d[%.%d]*)%s*,%s*(%-?%d[%.%d]*)")
									shp = ke.shape.displace(shp, {x = tonumber(dx), y = tonumber(dy), mode = "center"}).code
								end --"\\clip(ke.shape.circle, 120, -86)" relativo al (0, 0)
								return ("%s(%s)"):format(tag, shp)
							end
							return tag .. val
						end
					},
					[10] = {{"(%-?%d+%.%d+)"}, function(num) return ke.math.round(num, ROUND_NUM) end}, --round num tag
					[11] = {{"(\\%d?a[lpha]*)(%d[%.%d]*)"}, function(tag, val) return tag .. ke.alpha.ass(val) end}, --num to alpha
				} --str = "\\blur4\\34cs~"
				for _, cap in ipairs(changes) do
					for k, v in pairs(cap[1]) do
						local pattern = type(k) == "number" and v or k
						if cap[3] then
							for _, add in ipairs(cap[3]) do
								local padd = ("(%s)(%s)"):format(pattern, add)
								str = str:gsub(padd, cap[2])
							end
						else
							str = str:gsub(pattern, cap[2])
						end
					end
				end
				return str
				--]]
			end, --ke.tag.dark("\\blur4\\t(\\34cs~\\bordR(5)\\34a56)")
			
			only = function(conditions, ...)
				--retorna los parámetros dados según las condiciones indicadas
				conditions = type(conditions) == "function" and conditions() or conditions
				local exits = type(...) == "table" and ... or {...}
				if type(conditions) == "table" then
					for i = 1, #conditions do
						if conditions[i] then return exits[i] end
					end
					if #exits > #conditions then
						return exits[#conditions + 1]
					end
					return type(exits[#exits]) == "number" and 0 or ""
				end
				if conditions then return exits[1] end
				return exits[2] or (type(exits[1]) == "number" and 0 or "")
			end,
			
			clip = function(left, top, width, height)
				local loop = ke.infofx.data.loop
				local l, j = ke.infofx.data.l, ke.infofx.data.j
				left, width = left or l.left, width or l.width
				top, height = top or l.top, height or l.height
				local lw, lh = loop[1], loop[2] or 1
				local offset = l.outline + l.shadow
				local left_x, top_y = left - offset, top - offset
				local size_W, size_H = (width + 2 * offset) / lw, (height + 2 * offset) / lh
				local cx1 = ke.math.round(left_x + ((j - 1) % lw) * size_W, ROUND_NUM)
				local cx2 = ke.math.round(left_x + ((j - 1) % lw + 1) * size_W, ROUND_NUM)
				local cy1 = ke.math.round(top_y + (math.ceil(j / lw) - 1) * size_H, ROUND_NUM)
				local cy2 = ke.math.round(top_y + (math.ceil(j / lw)) * size_H, ROUND_NUM)
				return ("\\clip(%s,%s,%s,%s)"):format(cx1, cy1, cx2, cy2)
			end,
			
			move = function(configs)
				local fx, l = ke.infofx.data.fx, ke.infofx.data.l
				local onemove = function(onepack)
					local relative, points = type(onepack.relative) == "nil" or onepack.relative
					if onepack.shape then --smove: shape
						local smove, shp = ke.shape.new(onepack.shape):redraw(7.5, "bezier"), ke.recall.memory.shp
						points = ke.recall.memory.pnt
						if not shp then
							points, shp = smove.pnt, ke.recall.remember("shp", smove)
							local add = {relative and fx.center - points[1].x or 0, relative and fx.middle - points[1].y or 0}
							points = ke.recall.remember("pnt", ke.shape.point.group(points, function(p, get, add) return p + add end, add))
						end --ke.tag.move(ke.shape.circle)
					elseif onepack.random then --rmove: random
						local ts = onepack.times or fx.time_dur
						ts = type(ts) == "number" and {0, ts} or ts
						local dx, dy = onepack.random.dx or 10, onepack.random.dy or 10
						local dur, step = onepack.random.dur or frame_dur, onepack.random.step or 1
						local total, add = ts[2] - ts[1], relative and {fx.center, fx.middle} or {0, 0}
						local n = math.ceil(total / dur) - 1
						points = n > 0 and ke.shape.point.rand(nil, {n = n, dx = dx, dy = dy, step = step, sign = true}) or {}
						table.insert(points, 1, ke.shape.point.new({x = 0, y = 0}))
						table.insert(points, ke.shape.point.new({x = 0, y = 0}))
						points = ke.shape.point.group(points, function(p, get, add) return p + add end, add)
					elseif onepack.points then --pmove: points
						points = ke.table.get(onepack.points, "topoint")
						points = relative and ke.shape.point.group(points, function(p, get, add) return p + add end, {fx.center, fx.middle}) or points
					end --ke.tag.move({{random = {dur = 50}, times = {0, 600}}, {random = {dur = 50}, times = {fx.dur - 600, fx.dur}}})
					local ts, times = onepack.times or fx.time_dur, {}
					ts = type(ts) == "number" and {0, ts} or ts
					local total, n = ts[2] - ts[1], #points - 1
					for i = 1, n do
						local t1 = ke.math.normalize((i - 1) / n, ts.accel, ts.shape)
						local t2 = ke.math.normalize((i - 0) / n, ts.accel, ts.shape)
						times[i] = {ts[1] + total * t1, ts[1] + total * t2}
					end --onepack.times: {ini, fin, accel = [], shape = []}
					local add = {-fx.width / 2, 3 * fx.height / 2 - l.descent}
					points = ke.shape.point.group(points, function(p, get, add) return p + add end, add)
					local buinding = ke.shape.point.group(points, "bounding")
					return {points, times, ke.shape.point.new(buinding[1], buinding[2])}
				end
				local tagmoves = {}
				if type(configs) == "table" then
					local move = (configs.shape or configs.random or configs.points) and configs or nil
					tagmoves[1] = move and onemove(move) or nil
				elseif type(configs) == "string" then --shape
					tagmoves[1] = onemove({shape = configs})
				end
				tagmoves = not tagmoves[1] and ke.table.iter(configs, function(k, v) return onemove(v) end, {start = {}}) or tagmoves
				local minxy = ke.table.iter(tagmoves, function(i, v) return v[3] end, {start = {}, i = {1, #tagmoves}})
				local x0, y0 = table.unpack(ke.shape.point.group(minxy, "bounding"))
				x0, y0 = x0 >= 0 and 0 or x0, (y0 > 0 and y0 <= fx.height) and -y0 or (y0 >= 0 and 0 or y0)
				local tags = ("\\an7\\pos(%s,%s)\\q2"):format(x0, y0 - fx.height)
				for i, pack in ipairs(tagmoves) do
					local points, times = pack[1], pack[2]
					points = ke.shape.point.group(points, function(p, get, add) return p + add end, {-x0, -y0})
					if i == 1 then
						tags = tags .. ("\\fscx%s\\fscy%s"):format(points[1].x, points[1].y)
					end
					for k = 2, #points do
						tags = tags .. ("\\t(%s,%s,\\fscx%s\\fscy%s)"):format(times[k - 1][1], times[k - 1][2], points[k].x, points[k].y)
					end
				end
				tags = tags .. "\\p1}m 0 0 m 100 100 {\\p0\\r"
				return tags --ke.tag.move({random = {dur = 50}, times = 1000})
			end,
			
			oscill = function(configs, ...)
				--generates transformations that oscillate between the values ​​of the entered tags
				local fx = ke.infofx.data.fx
				local time_ini, time_fin, total = 0, fx.time_dur
				local index, dur_del1, dur_del2 = 1, ke.infofx.data.frame_dur
				local accel, dilat, offset, time_off, tags = 1, 0, 0, 0, {...}
				local times, fxdelay = {0, fx.time_dur}, dur_del1
				if configs and type(configs) == "table" then
					times, index = configs.times or times, configs.index or index
					dilat, offset = configs.dilat or dilat, configs.offset or offset
					accel, fxdelay = configs.accel or accel, configs.delay or fxdelay
				end
				times = type(times) == "number" and {0, times} or times
				times = type(times) == "function" and times() or times
				time_ini, time_fin = times[1], times[2]
				if type(times[1]) == "table" then
					local multi_oscill = {}
					for i = 1, #times do
						configs.times = times[i]
						multi_oscill[i] = ke.tag.oscill(configs, ...)
					end --recurse
					return table.concat(multi_oscill)
				end --ke.tag.oscill({times = {{0, 500}, {fx.time_dur - 500, fx.time_dur}}, delay = 100}, "\\1cR()")
				total = time_fin - time_ini
				dur_del1 = type(fxdelay) == "function" and fxdelay() or fxdelay
				dur_del2 = dur_del1
				dur_del1 = type(fxdelay) == "table" and fxdelay[1] or dur_del1
				dur_del2 = type(fxdelay) == "table" and fxdelay[2] or dur_del2
				tags = type(...) == "table" and ... or tags
				local time_i, tags_fx, tag_osc, element = 0, "", ""
				local i, dlt, delay, dur, off = 0, dilat
				while total > 0 do
					delay = dlt + (type(fxdelay) == "function" and fxdelay(i) or dur_del1)
					dur = type(fxdelay) == "function" and delay or dur_del2
					time_i = time_ini
					if time_i >= time_fin then
						break
					end --ke.tag.oscill({times = {0, 500}, delay = 100}, "\\1cR()")
					element = tags[(index + i - 1) % #tags + 1]
					element = type(element) == "function" and element(i) or element
					tags_fx = tags_fx .. ("\\t(%s,%s,%s,%s)"):format(time_i, time_i + dur, accel, element)
					total = total - delay
					off = (i + 1) % #tags == 0 and offset or 0
					off = type(off) == "function" and off(i) or off
					time_ini = time_i + delay + off
					dlt = dlt + dilat
					i = i + 1
					--ke.tag.oscill({times = {ke.math.rand(800), fx.time_dur}, delay = {100, 0}, offset = mydur}, "\\alpha255", "\\alpha0")
					--mydur = function() return ke.math.rand(500, 2000, 20) end
				end
				tags_fx = ke.string.i(tags_fx)
				return tags_fx
			end,
			
			set = function(times, events)
				local fx = ke.infofx.data.fx
				times = type(times) == "function" and times() or times
				times = ke.time.HMS_to_ms(times)
				local function tag_last(str)
					local tags = {--borra los tags repetidos y solo deja el último de cada uno de ellos
						[01] = "\\fscxy",	[02] = "\\faxy",	[03] = "\\frxyz",	[04] = "\\frxy",	[05] = "\\frxz",	[06] = "\\fryz",
						[07] = "\\bs",		[08] = "\\134a",	[09] = "\\13a",		[10] = "\\14a",		[11] = "\\34a",		[12] = "\\134c",
						[13] = "\\13c",		[14] = "\\14c",		[15] = "\\34c",		[16] = "\\1c",		[17] = "\\2c",		[18] = "\\3c",
						[19] = "\\4c",		[20] = "\\1a",		[21] = "\\2a",		[22] = "\\3a",		[23] = "\\4a",		[24] = "\\alpha",
						[25] = "\\fsp",		[26] = "\\blur",	[27] = "\\bord",	[28] = "\\xbord",	[29] = "\\ybord",	[30] = "\\xybord",
						[31] = "\\be",		[32] = "\\fe",		[33] = "\\shad",	[34] = "\\xshad",	[35] = "\\yshad",	[36] = "\\xyshad",
						[37] = "\\fn",		[38] = "\\fax",		[39] = "\\fay",		[40] = "\\frx",		[41] = "\\fry",		[42] = "\\frz?",
						[43] = "\\fscx",	[44] = "\\fscy",	[45] = "\\fs",		[46] = "\\b",		[47] = "\\i",		[48] = "\\u",
						[49] = "\\s",		[50] = "\\p",		[51] = "\\clip",	[52] = "\\iclip"
					}
					local v = {"%-?[%d&]^*[%.%dH%x&]*", "R%b()", "%b()"}
					for i = 1, #tags do
						str = ke.string.change(str, {tags[i] .. v[1], tags[i] .. v[2], tags[i] .. v[3]}, {nochange = -1, protect = "\\t%b()"})
					end
					return str
				end
				local t2, accel, fxreturn = 1, 1, {}
				for i = 1, #times do
					local k = (i - 1) % #events + 1
					events[k] = type(events[k]) == "function" and events[k]() or events[k]
					local Transfos = ke.string.array(events[k], "\\t%b()")	--tabla de transfos
					if type(times[i]) == "table" then						--tiempos de las transfos
						t2 = times[i][2] - times[i][1]
						accel = times[i][3] or 1
					end
					fxreturn[i] = ("\\t(0,%s,%s,%s)"):format(t2, accel, events[k]:gsub("\\t%b()", "")) .. table.concat(Transfos)
					fxreturn[i] = fxreturn[i]:gsub("\\t%b()",
						function(tagst)
							local time1, time2
							tagst = tagst:gsub("(\\t)%(%s?(%d[%.%d]*),%s?(%d[%.%d]*)",
								function(tag, t1, t2)
									time1 = t1 + times[i] - fx.time_ini
									time2 = t2 + times[i] - fx.time_ini
									return ("%s(%s,%s"):format(tag, time1, time2)
								end
							)
							if time2 <= 0 then
								return tagst:match("%b()"):sub(2, -2):match("\\%w+[%S]*")
							end
							return time1 >= fx.time_fin and "" or tagst
						end
					)
				end
				return tag_last(table.concat(fxreturn))
			end,
			
			glitter = function(deration, extratags1, extratags2)
				local fx = ke.infofx.data.fx
				local i, t, t1, t2, t3, t4, tags = 0, 0, 0, 0, 0, 0, "\\shad0"
				local time1 = type(deration) == "function" and deration()[1]
				or (type(deration) == "table" and deration[1]) or 0
				local time2 = type(deration) == "function" and deration()[2]
				or (type(deration) == "table" and deration[2]) or deration or fx.time_dur
				local time_tot, eti, etf, size1, size2 = time2 - time1
				while time_tot > t do
					t1 = t + ke.math.rand(1, time_tot / 2, 0.01)
					t2 = t1 + 1
					t3 = t2 + 41
					t4 = t3 + 102
					size1, size2 = ke.math.rand(150, 250, 0.01), ke.math.rand(50, 150, 0.01)
					eti = type(extratags1) == "function" and extratags1(i) or extratags1 or ""
					etf = type(extratags2) == "function" and extratags2(i) or extratags2 or ""
					t4 = t4 > time_tot and time_tot or t4
					tags = tags .. ("\\t(%d,%d,%s\\fscx%d\\fscy%d)\\t(%d,%d,%s\\fscx%d\\fscy%d)"):format(
						time1 + t1, time1 + t2, eti, size1, size1, time1 + t3, time1 + t4, etf, size2, size2
					)
					i, t = i + 1, t4
				end
				return ke.string.i(tags) 
			end, --ke.tag.glitter()
			
			array = function(str)
				local tags = ke.string.capture(str, {"\\[%d]*%a+%-?[%d&]^*[%.%dH%x&]*", "\\[%d]*[^t%W]%a+%b()"}, {protect = "\\t%b()", include = true})
				local pack, k = ke.table.new(), ke.math.count()
				local gettimes = function(tag)
					local tbl = ke.string.toval(("{%s}"):format(tag:match("\\t%((.-)\\")))	--times \\t
					local ttags = tag:match("\\t(%b())"):sub(2, -2):match("\\.+")			--tags in \\t
					local t1, t2, ac = 0, ke.infofx.data.fx.time_dur, 1
					ac = tbl[3] or (#tbl == 1 and tbl[1] or ac)
					t2 = tbl[2] or t2
					t1 = #tbl > 1 and tbl[1] or t1
					return {t1, t2, ac}, ttags
				end
				for i, v in ipairs(tags) do
					local cap1, cap2 = v:match("(\\[%d]*%l+)(R?%b())")
					if not cap2 then
						cap1, cap2 = v:match("(\\[%d]*%l+)(%-?[%d&]^*[%.%dH%x&]*)")
					end
					pack[i] = {tag = cap1, val = cap2}
					if pack[i].tag == "\\t" then
						pack[i].tag = pack[i].tag .. tostring(k())
						pack[i].val = ke.tag.array(pack[i].val)
						pack[i].times, pack[i].tags = gettimes(v)
					end --"\\t%(([^\\]*)\\"
				end --ke.tag.array("\\t(0,80,\\1c&HFF00FF&\\bord1\\alpha&HFF&)")
				return pack
			end, --str = "\\frz-32\\blur-2\\1a&HFF&\\bordR(2,6)\\org(80,90)\\iclip(m 0 0 l 0 100 l 100 100 )\\t(0,80,\\1c&HFF00FF&\\bord1\\alpha&HFF&)\\p1"
			
			ipol = function(tags, t, accel, shape, size)
				for k, v in ipairs(tags) do
					tags[k] = ke.tag.array(ke.tag.dark(v))
				end
				local taginsert = function(tags, ins)
					--inserts a tag if it does not belong to a table
					ishere = false
					for i = 1, #tags do
						if tags[i].tag == ins.tag then
							ishere = true
							break
						end
					end
					if not ishere then
						table.insert(tags, ke.table.copy(ins))
					end
				end
				local ordertags = function(tags, order)
					--reorders the elements of one table relative to another
					local aux = ke.table.copy(tags)
					tags = {}
					for i, v in ipairs(order) do
						for k, val in ipairs(aux) do
							if val.tag == v.tag then
								table.insert(tags, i, val)
								break
							end
						end
					end
					return tags
				end
				local functipol = function(tags, t, accel, shape, size)
					--tags interpolation
					local ipol = {number = ke.math.ipol, funct = ke.math.ipol, color = ke.color.ipol, alpha = ke.alpha.ipol, shape = ke.shape.ipol}
					local adaptval = function(val, tag, istype)
						if istype == "funct" then
							val = "(" .. table.concat(val, ",") .. ")"
						elseif istype == "shape" then
							val = "(" .. val .. ")"
						end
						return ("%s%s"):format(tag, val)
					end
					local valstype = function(val)
						local istype = "number"
						istype = val:match(",") and "funct" or istype
						istype = val:match("&H%x+&") and "color" or istype
						istype = val:match("&H%x%x&") and "alpha" or istype
						istype = val:match("m%s+%-?%d[%.%-%d blm]*") and "shape" or istype
						return istype
					end
					for k, v in ipairs(tags) do
						tags[k].type = valstype(v[1])
						if tags[k].type == "number" then
							for i, val in ipairs(v) do
								tags[k][i] = tonumber(val)
							end
						elseif tags[k].type == "funct" then
							for i, val in ipairs(v) do
								tags[k][i] = ke.string.toval("{" .. val:sub(2, -2) .. "}")
							end
						elseif tags[k].type == "shape" then
							for i, val in ipairs(v) do
								tags[k][i] = val:match("m%s+%-?%d[%.%-%d blm]*")
							end
						end
					end
					local result, stringtags = {}, ""
					for k, v in ipairs(tags) do
						local ipolval, ipoltag, ipoltype = ipol[v.type], v.tag, v.type
						v.tag, v.type = nil
						result[k] = adaptval(ipolval(v, t, accel, shape, size), ipoltag, ipoltype)
					end
					return table.concat(result)
				end
				for i = 2, #tags do
					for k, v in ipairs(tags[i]) do
						taginsert(tags[1], v)
					end
				end
				for i = 2, #tags do
					for k, v in ipairs(tags[i - 1]) do
						taginsert(tags[i], v)
					end
					tags[i] = ordertags(tags[i], tags[1])
				end
				local datatags, i = {}, 1
				while tags[1][i] do
					datatags[i] = {}
					for k = 1, #tags do
						if k == 1 then
							datatags[i].tag = tags[k][i].tag
						end
						table.insert(datatags[i], tags[k][i].val)
					end
					i = i + 1
				end
				return functipol(datatags, t)
			end, --ke.tag.ipol({"\\1a&HAA&\\blur3\\fr45", "\\1a&HFF&\\clip(m 0 0 l 0 20 20 20 )\\org(40,50)\\blur0", "\\foo-4"}, 0.25)
			
		},
		
		time = {
			
			HMS_to_ms = function(HMS)
				--from HMS to ms format time
				if type(HMS) == "table" then
					return ke.table.recurse(ke.time.HMS_to_ms, HMS)
				end --recurse
				HMS = type(HMS) == "function" and HMS() or HMS or 0
				if type(HMS) == "string" and HMS:match("%d+%:%d+%:%d+%.%d+") then
					local H, M, S, ms = HMS:match("(%d+)%:(%d+)%:(%d+)%.(%d+)")
					ms = ms:len() == 2 and 10 * ms or (ms:len( ) == 1 and 100 * ms or ms)
					return H * 3600000 + M * 60000 + S * 1000 + ms
				end
				return tonumber(HMS) and tonumber(HMS) or HMS
			end, --ke.time.HMS_to_ms({"0:00:34.952", "0:00:44.920", "0:00:48.882"})
			
			ms_to_HMS = function(ms)
				--convierte el tiempo de ms a formato HMS
				ms = ke.math.__init(ms, 0)
				if type(ms) == "table" then
					return ke.table.recurse(ke.time.ms_to_HMS, ms)
				end --recurse
				local tms, H, M, S = ke.math.round(ms), 0, 0, 0
				H = math.floor(tms / 3600000)
				tms = tms - H * 3600000
				M = math.floor(tms / 60000)
				tms = tms - M * 60000
				S = math.floor(tms / 1000)
				tms = tms - S * 1000 --ke.time.ms_to_HMS({540.945, 5645, 27432})
				M = M < 10 and "0" .. M or M
				S = S < 10 and "0" .. S or S
				tms = tostring(tms):len() == 1 and "00" .. tms or (tostring(tms):len() == 2 and "0" .. tms or tms)
				return ("%s:%s:%s.%s"):format(H, M, S, tms)
			end, --ke.time.ms_to_HMS((j - 1) * 41.7)
			
			time_to_frame = function(time)
				--retorna la cantidad de frames que hay en un tiempo determinado
				time = type(time) == "function" and time() or time or 0
				if type(time) == "table" then
					return ke.table.recurse(ke.time.time_to_frame, time)
				end --recurse
				time = tostring(time)
				if time:match("%d+%:%d+%:%d+%.%d+") then
					time = type(ke.time.HMS_to_ms(time)) == "table" and ke.time.HMS_to_ms(time)[1] or ke.time.HMS_to_ms(time)
				end --ke.time.time_to_frame({3000, "0:00:25.673"})
				return math.ceil(time / frame_dur)
			end, --ke.time.time_to_frame(2000)
			
			frame_to_ms = function(frames)
				--convierte la cantidad de frames en un tiempo en formato ms
				frames = ke.math.__init(frames, 0)
				if type(frames) == "table" then
					return ke.table.recurse(ke.time.frame_to_ms, frames)
				end --recurse
				return ke.math.round(frames * frame_dur, 2)
			end, --ke.time.frame_to_ms({2365, 128, 82351})
			
			frame_to_HMS = function(frames)
				--convierte la cantidad de frames en un tiempo en formato HMS
				frames = ke.math.__init(frames, 0)
				if type(frames) == "table" then
					return ke.table.recurse(ke.time.frame_to_HMS, frames)
				end --recurse
				return ke.time.ms_to_HMS(ke.time.frame_to_ms(frames))
			end, --ke.time.frame_to_HMS({35, 240, {4532, {24, 276}, 9574}})
			
			ipol = function(times, configs)
				times = ke.time.HMS_to_ms(times)
				configs = configs or {n = nil, accel = 1, points = nil, numbers = nil}
				local result, groups = ke.table.new(), ke.table.new()
				local couples = function(k, v, t) return (type(k) == "number" and k < #t) and {v, t[k + 1]} or nil end
				if type(times) == "number" then --times --> "number"
					groups:insert({0, times})
				elseif type(times) == "table" and times.segs then --times --> {segs = {{seg1}, {seg2}, ...}}
					for k, v in pairs(times.segs) do
						groups:insert(v)
					end
				elseif ke.table.type(times) == "table" then --times --> {{lap1}, {lap2}, {lap3}, ...}
					result:insert(times)
				elseif ke.table.type(times) == "number" then --times --> {ini, fin}
					groups:insert(ke.table.filter(times, couples), nil, true)
				end --times --> {t1, t2, t3, ...}
				if #result == 0 then
					local accel = type(configs) == "table" and configs.accel or 1
					if type(configs) == "table" and (configs.points or configs.numbers) then
						local values = {points = configs.points, numbers = configs.numbers}
						local function ipoltime(values, v, accel)
							local t0, dur = v[1], v[2] - v[1]
							local total, accum, aux, ts = 0, 0, {t0}, {}
							local vals = values.numbers or values.points
							local ispoints = values.points and 1 or 0
							if ispoints == 1 then
								vals, aux[0] = ke.shape.point.group(vals, "lengths"), t0
								total = vals.total
								for i = 1, #vals do
									accum = accum + vals[i]
									local u = accum / total
									aux[i] = t0 + dur * (type(accel) == "function" and accel(u) or u ^ accel)
									ts[i] = {aux[i - 1], aux[i]}
								end --ke.time.ipol({200, 500}, {points = ke.shape.new(ke.shape.rectangle):points()})
							else
								for i = 2, #vals do
									total = total + math.abs(vals[i] - vals[i - 1])
								end
								for i = 2, #vals do
									accum = accum + math.abs(vals[i] - vals[i - 1])
									local u = accum / total
									aux[i] = t0 + dur * (type(accel) == "function" and accel(u) or u ^ accel)
									ts[i - 1] = {aux[i - 1], aux[i]}
								end
							end --ke.time.ipol({segs = {{0, 100}, {400,500}}}, {points = ke.shape.new(ke.shape.rectangle):points()})
							return ts
						end --ke.time.ipol(1000, {numbers = {100,0,100,0}, accel = 1.2})
						for k, v in ipairs(groups) do
							result:insert(ipoltime(values, v, accel))
						end
						return result
					end
					local n = type(configs) == "number" and configs or nil
					n = type(configs) == "table" and configs.n or n
					if not n then
						result = groups
					else
						for k, v in ipairs(groups) do
							v = ke.math.ipol(v, nil, accel, nil, n + 1)
							result:insert(ke.table.filter(v, couples))
						end
					end
				end
				return result
			end,
			
			middle = function(delay)
				local delay = delay or 30
				local fx = ke.infofx.data.fx
				return fx.i <= (fx.n + 1) / 2 and delay * (fx.i - 1) - 200 or delay * (fx.n - fx.i + 0.5) - 200
			end,
			
			leadin = function(delay)
				local delay = delay or 40
				local fx = ke.infofx.data.fx
				return delay * (fx.i - 1) - 200
			end,
			
			leadout = function(delay)
				local delay = delay or 40
				local fx = ke.infofx.data.fx
				return delay * (fx.i - fx.n - 1) + 200
			end,
			
			loop = function(delay, mode)
				local mode = mode or "leadin"
				local delay = delay or 30
				local j, maxj = ke.infofx.data.j, ke.infofx.data.maxj
				if mode == "leadin" then
					return delay * (j - 1) - 200
				elseif mode == "leadout" then
					return delay * (j - maxj - 1) + 200
				elseif mode == "middle" then
					return j <= (maxj + 1) / 2 and delay * (j - 1) - 200 or delay * (maxj - j + 0.5) - 200
				end --ke.time.loop(40)
				return delay
			end,
			
		},
		
		decode = {
			
			config = include("kelibs\\newkara_ffi.lua"),
			
			utf8 = {
				
				chars = function(s)
					--creates iterator through UTF8 characters
					local char_i, s_pos, s_len = 0, 1, #s
					local charrange = function(s, i)
						local byte = s:byte(i)
						return not byte and 0 or byte < 192 and 1 or byte < 224 and 2 or byte < 240 and 3 or byte < 248 and 4 or byte < 252 and 5 or 6
					end --UTF8 character range at string codepoint
					return function()
						if s_pos <= s_len then
							local cur_pos = s_pos
							s_pos = s_pos + charrange(s, s_pos)
							if s_pos - 1 <= s_len then
								char_i = char_i + 1
								return char_i, s:sub(cur_pos, s_pos - 1)
							end
						end
					end
				end,
				
				len = function(s)
					--get UTF8 characters number in string
					local n = 0
					for _ in ke.decode.utf8.chars(s) do
						n = n + 1
					end
					return n
				end,
				
				utf8_to_utf16 = function(s)
					local wlen = ke.decode.config.ffi.C.MultiByteToWideChar(ke.decode.config.ffi.C.CP_UTF8X2, 0x0, s, -1, nil, 0)
					local ws = ke.decode.config.ffi.new("wchar_t[?]", wlen)
					ke.decode.config.ffi.C.MultiByteToWideChar(ke.decode.config.ffi.C.CP_UTF8X2, 0x0, s, -1, ws, wlen)
					return ws
				end,
				
				utf16_to_utf8 = function(ws)
					local slen = ke.decode.config.ffi.C.WideCharToMultiByte(ke.decode.config.ffi.C.CP_UTF8X2, 0x0, ws, -1, nil, 0, nil, nil)
					local s = ke.decode.config.ffi.new("char[?]", slen)
					ke.decode.config.ffi.C.WideCharToMultiByte(ke.decode.config.ffi.C.CP_UTF8X2, 0x0, ws, -1, s, slen, nil, nil)
					return ke.decode.config.ffi.string(s)
				end,
				
			},
			
			create_font = function(configtxt)
				local family, bold, italic, underline, strikeout, size, xscale, yscale, hspace = table.unpack(configtxt)
				--creates font
				if type(family) ~= "string" or type(bold) ~= "boolean" or type(italic) ~= "boolean" or type(underline) ~= "boolean" or type(strikeout) ~= "boolean" or type(size) ~= "number" or size <= 0 or
					(xscale ~= nil and type(xscale) ~= "number") or (yscale ~= nil and type(yscale) ~= "number") or (hspace ~= nil and type(hspace) ~= "number") then
					error("expected family, bold, italic, underline, strikeout, size and optional horizontal & vertical scale and intercharacter space", 2)
				end
				local xscale = not xscale and 1 or xscale
				local yscale = not yscale and 1 or yscale
				local hspace = not hspace and 0 or hspace
				local upscale = FONT_PRECISION
				local downscale = 1 / upscale
				if ke.decode.config.ffi.os == "Windows" then
					local resources_deleter
					local dc = ke.decode.config.ffi.gc(ke.decode.config.ffi.C.CreateCompatibleDC(nil), function() resources_deleter() end)
					ke.decode.config.ffi.C.SetMapMode(dc, ke.decode.config.ffi.C.MM_TEXT2X)
					ke.decode.config.ffi.C.SetBkMode(dc, ke.decode.config.ffi.C.TRANSPARENT2X)
					family = ke.decode.utf8.utf8_to_utf16(family)
					if ke.decode.config.ffi.C.wcslen(family) > 31 then
						error("family name to long", 2)
					end
					local font = ke.decode.config.ffi.C.CreateFontW(
						size * upscale,									--nHeight
						0,												--nWidth
						0,												--nEscapement
						0,												--nOrientation
						bold and ke.decode.config.ffi.C.FW_BOLD2X or ke.decode.config.ffi.C.FW_NORMAL2X,	--fnWeight
						italic and 1 or 0,								--fdwItalic
						underline and 1 or 0,							--fdwUnderline
						strikeout and 1 or 0,							--fdwStrikeOut
						ke.decode.config.ffi.C.DEFAULT_CHARSET2X,						--fdwCharSet
						ke.decode.config.ffi.C.OUT_TT_PRECIS2X,							--fdwOutputPrecision
						ke.decode.config.ffi.C.CLIP_DEFAULT_PRECIS2X,					--fdwClipPrecision
						ke.decode.config.ffi.C.ANTIALIASED_QUALITY2X,					--fdwQuality
						ke.decode.config.ffi.C.DEFAULT_PITCH2X + ke.decode.config.ffi.C.FF_DONTCARE2X,	--fdwPitchAndFamily
						family
					)
					local old_font = ke.decode.config.ffi.C.SelectObject(dc, font)
					resources_deleter = function()
						ke.decode.config.ffi.C.SelectObject(dc, old_font)
						ke.decode.config.ffi.C.DeleteObject(font)
						ke.decode.config.ffi.C.DeleteDC(dc)
					end
					return {
						metrics = function()
							local metrics = ke.decode.config.ffi.new("TEXTMETRICW[1]")
							ke.decode.config.ffi.C.GetTextMetricsW(dc, metrics)
							return {
								height = metrics[0].tmHeight * downscale * yscale,
								ascent = metrics[0].tmAscent * downscale * yscale,
								descent = metrics[0].tmDescent * downscale * yscale,
								internal_leading = metrics[0].tmInternalLeading * downscale * yscale,
								external_leading = metrics[0].tmExternalLeading * downscale * yscale
							}
						end,
						text_extents = function(text)
							if type(text) ~= "string" then
								error("text expected", 2)
							end
							text = ke.decode.utf8.utf8_to_utf16(text)
							local text_len = ke.decode.config.ffi.C.wcslen(text)
							local size = ke.decode.config.ffi.new("SIZE[1]")
							ke.decode.config.ffi.C.GetTextExtentPoint32W(dc, text, text_len, size)
							return {
								width = (size[0].cx * downscale + hspace * text_len) * xscale,
								height = size[0].cy * downscale * yscale
							}
						end,
						
						text_to_shape = function(text)
							--Converts text to ASS shape
							if type(text) ~= "string" then
								error("text expected", 2)
							end
							local shape, shape_n = {}, 0
							text = ke.decode.utf8.utf8_to_utf16(text)
							local text_len = ke.decode.config.ffi.C.wcslen(text)
							if text_len > 8192 then
								error("text too long", 2)
							end
							local char_widths
							if hspace ~= 0 then
								char_widths = ke.decode.config.ffi.new("INT[?]", text_len)
								local size, space = ke.decode.config.ffi.new("SIZE[1]"), hspace * upscale
								for i = 0, text_len - 1 do
									ke.decode.config.ffi.C.GetTextExtentPoint32W(dc, text + i, 1, size)
									char_widths[i] = size[0].cx + space
								end
							end
							ke.decode.config.ffi.C.BeginPath(dc)
							ke.decode.config.ffi.C.ExtTextOutW(dc, 0, 0, 0x0, nil, text, text_len, char_widths)
							ke.decode.config.ffi.C.EndPath(dc)
							local points_n = ke.decode.config.ffi.C.GetPath(dc, nil, nil, 0)
							if points_n > 0 then
								local points, types = ke.decode.config.ffi.new("POINT[?]", points_n), ke.decode.config.ffi.new("BYTE[?]", points_n)
								ke.decode.config.ffi.C.GetPath(dc, points, types, points_n)
								local i, last_type, cur_type, cur_point = 0
								while i < points_n do
									cur_type, cur_point = types[i], points[i]
									if cur_type == ke.decode.config.ffi.C.PT_MOVETO2X then
										if last_type ~= ke.decode.config.ffi.C.PT_MOVETO2X then
											shape_n = shape_n + 1
											shape[shape_n] = "m"
											last_type = cur_type
										end
										shape[shape_n + 1] = ke.math.round(cur_point.x * downscale * xscale, FP_PRECISION)
										shape[shape_n + 2] = ke.math.round(cur_point.y * downscale * yscale, FP_PRECISION)
										shape_n = shape_n + 2
										i = i + 1
									elseif cur_type == ke.decode.config.ffi.C.PT_LINETO2X or cur_type == (ke.decode.config.ffi.C.PT_LINETO2X + ke.decode.config.ffi.C.PT_CLOSEFIGURE2X) then
										if last_type ~= ke.decode.config.ffi.C.PT_LINETO2X then
											shape_n = shape_n + 1
											shape[shape_n] = "l"
											last_type = cur_type
										end
										shape[shape_n + 1] = ke.math.round(cur_point.x * downscale * xscale, FP_PRECISION)
										shape[shape_n + 2] = ke.math.round(cur_point.y * downscale * yscale, FP_PRECISION)
										shape_n = shape_n + 2
										i = i + 1
									elseif cur_type == ke.decode.config.ffi.C.PT_BEZIERTO2X or cur_type == (ke.decode.config.ffi.C.PT_BEZIERTO2X + ke.decode.config.ffi.C.PT_CLOSEFIGURE2X) then
										if last_type ~= ke.decode.config.ffi.C.PT_BEZIERTO2X then
											shape_n = shape_n + 1
											shape[shape_n] = "b"
											last_type = cur_type
										end
										shape[shape_n + 1] = ke.math.round(cur_point.x * downscale * xscale, FP_PRECISION)
										shape[shape_n + 2] = ke.math.round(cur_point.y * downscale * yscale, FP_PRECISION)
										shape[shape_n + 3] = ke.math.round(points[i + 1].x * downscale * xscale, FP_PRECISION)
										shape[shape_n + 4] = ke.math.round(points[i + 1].y * downscale * yscale, FP_PRECISION)
										shape[shape_n + 5] = ke.math.round(points[i + 2].x * downscale * xscale, FP_PRECISION)
										shape[shape_n + 6] = ke.math.round(points[i + 2].y * downscale * yscale, FP_PRECISION)
										shape_n = shape_n + 6
										i = i + 3
									else
										i = i + 1
									end
									if cur_type % 2 == 1 then
										shape_n = shape_n + 1
										shape[shape_n] = "c"
									end
								end
							end
							ke.decode.config.ffi.C.AbortPath(dc)
							return table.concat(shape, " ")
						end
					}
				else
					if not ke.decode.config.pangocairo then
						error("pangocairo library couldn't be loaded", 2)
					end
					local surface = ke.decode.config.pangocairo.cairo_image_surface_create(ke.decode.config.ffi.C.CAIRO_FORMAT_A8X, 1, 1)
					local context = ke.decode.config.pangocairo.cairo_create(surface)
					local layout
					layout = ke.decode.config.ffi.gc(ke.decode.config.pangocairo.pango_cairo_create_layout(context), function()
						ke.decode.config.pangocairo.g_object_unref(layout)
						ke.decode.config.pangocairo.cairo_destroy(context)
						ke.decode.config.pangocairo.cairo_surface_destroy(surface)
					end)
					local font_desc = ke.decode.config.ffi.gc(ke.decode.config.pangocairo.pango_font_description_new(), ke.decode.config.pangocairo.pango_font_description_free)
					ke.decode.config.pangocairo.pango_font_description_set_family(font_desc, family)
					ke.decode.config.pangocairo.pango_font_description_set_weight(font_desc, bold and ke.decode.config.ffi.C.PANGO_WEIGHT_BOLD2 or ke.decode.config.ffi.C.PANGO_WEIGHT_NORMAL2)
					ke.decode.config.pangocairo.pango_font_description_set_style(font_desc, italic and ke.decode.config.ffi.C.PANGO_STYLE_ITALIC or ke.decode.config.ffi.C.PANGO_STYLE_NORMAL)
					ke.decode.config.pangocairo.pango_font_description_set_absolute_size(font_desc, size * ke.decode.config.ffi.C.PANGO_SCALE2 * upscale)
					ke.decode.config.pangocairo.pango_layout_set_font_description(layout, font_desc)
					local attr = ke.decode.config.ffi.gc(ke.decode.config.pangocairo.pango_attr_list_new(), ke.decode.config.pangocairo.pango_attr_list_unref)
					ke.decode.config.pangocairo.pango_attr_list_insert(attr, ke.decode.config.pangocairo.pango_attr_underline_new(underline and ke.decode.config.ffi.C.PANGO_UNDERLINE_SINGLE or ke.decode.config.ffi.C.PANGO_UNDERLINE_NONE))
					ke.decode.config.pangocairo.pango_attr_list_insert(attr, ke.decode.config.pangocairo.pango_attr_strikethrough_new(strikeout))
					ke.decode.config.pangocairo.pango_attr_list_insert(attr, ke.decode.config.pangocairo.pango_attr_letter_spacing_new(hspace * ke.decode.config.ffi.C.PANGO_SCALE2 * upscale))
					ke.decode.config.pangocairo.pango_layout_set_attributes(layout, attr)
					local fonthack_scale = 1
					return {
						metrics = function()
							local metrics = ke.decode.config.ffi.gc(ke.decode.config.pangocairo.pango_context_get_metrics(ke.decode.config.pangocairo.pango_layout_get_context(layout), ke.decode.config.pangocairo.pango_layout_get_font_description(layout), nil), ke.decode.config.pangocairo.pango_font_metrics_unref)
							local ascent, descent = ke.decode.config.pangocairo.pango_font_metrics_get_ascent(metrics) / ke.decode.config.ffi.C.PANGO_SCALE2 * downscale,
													ke.decode.config.pangocairo.pango_font_metrics_get_descent(metrics) / ke.decode.config.ffi.C.PANGO_SCALE2 * downscale
							return {
								height = (ascent + descent) * yscale * fonthack_scale,
								ascent = ascent * yscale * fonthack_scale,
								descent = descent * yscale * fonthack_scale,
								internal_leading = 0,
								external_leading = ke.decode.config.pangocairo.pango_layout_get_spacing(layout) / ke.decode.config.ffi.C.PANGO_SCALE2 * downscale * yscale * fonthack_scale
							}
						end,
						text_extents = function(text)
							if type(text) ~= "string" then
								error("text expected", 2)
							end
							ke.decode.config.pangocairo.pango_layout_set_text(layout, text, -1)
							local rect = ke.decode.config.ffi.new("PangoRectangle[1]")
							ke.decode.config.pangocairo.pango_layout_get_pixel_extents(layout, nil, rect)
							return {
								width = rect[0].width * downscale * xscale * fonthack_scale,
								height = rect[0].height * downscale * yscale * fonthack_scale
							}
						end,
						
						text_to_shape = function(text)
							if type(text) ~= "string" then
								error("text expected", 2)
							end
							ke.decode.config.pangocairo.cairo_save(context)
							ke.decode.config.pangocairo.cairo_scale(context, downscale * xscale * fonthack_scale, downscale * yscale * fonthack_scale)
							ke.decode.config.pangocairo.pango_layout_set_text(layout, text, -1)
							ke.decode.config.pangocairo.pango_cairo_layout_path(context, layout)
							ke.decode.config.pangocairo.cairo_restore(context)
							local shape, shape_n = {}, 0
							local path = ke.decode.config.ffi.gc(ke.decode.config.pangocairo.cairo_copy_path(context), ke.decode.config.pangocairo.cairo_path_destroy)
							if(path[0].status == ke.decode.config.ffi.C.CAIRO_STATUS_SUCCESS2) then
								local i, cur_type, last_type = 0
								while(i < path[0].num_data) do
									cur_type = path[0].data[i].header.type
									if cur_type == ke.decode.config.ffi.C.CAIRO_PATH_MOVE_TO then
										if cur_type ~= last_type then
											shape_n = shape_n + 1
											shape[shape_n] = "m"
										end
										shape[shape_n + 1] = ke.math.round(path[0].data[i + 1].point.x, FP_PRECISION)
										shape[shape_n + 2] = ke.math.round(path[0].data[i + 1].point.y, FP_PRECISION)
										shape_n = shape_n + 2
									elseif cur_type == ke.decode.config.ffi.C.CAIRO_PATH_LINE_TO then
										if cur_type ~= last_type then
											shape_n = shape_n + 1
											shape[shape_n] = "l"
										end
										shape[shape_n + 1] = ke.math.round(path[0].data[i + 1].point.x, FP_PRECISION)
										shape[shape_n + 2] = ke.math.round(path[0].data[i + 1].point.y, FP_PRECISION)
										shape_n = shape_n + 2
									elseif cur_type == ke.decode.config.ffi.C.CAIRO_PATH_CURVE_TO then
										if cur_type ~= last_type then
											shape_n = shape_n + 1
											shape[shape_n] = "b"
										end
										shape[shape_n + 1] = ke.math.round(path[0].data[i + 1].point.x, FP_PRECISION)
										shape[shape_n + 2] = ke.math.round(path[0].data[i + 1].point.y, FP_PRECISION)
										shape[shape_n + 3] = ke.math.round(path[0].data[i + 2].point.x, FP_PRECISION)
										shape[shape_n + 4] = ke.math.round(path[0].data[i + 2].point.y, FP_PRECISION)
										shape[shape_n + 5] = ke.math.round(path[0].data[i + 3].point.x, FP_PRECISION)
										shape[shape_n + 6] = ke.math.round(path[0].data[i + 3].point.y, FP_PRECISION)
										shape_n = shape_n + 6
									elseif cur_type == ke.decode.config.ffi.C.CAIRO_PATH_CLOSE_PATH then
										if cur_type ~= last_type then
											shape_n = shape_n + 1
											shape[shape_n] = "c"
										end
									end
									last_type = cur_type
									i = i + path[0].data[i].header.length
								end
							end
							ke.decode.config.pangocairo.cairo_new_path(context)
							return table.concat(shape, " ")
						end
					}
				end
			end,
			
		},
		
		image = {
			
			to_pixels = function(png)
				local image = require("ILL.IMG")
				local png = png or "C:\\Users\\victo\\Escritorio\\effector2\\demo4.png"
				local img = image.LIBPNG(png):decode()
				local w, h = img.width, img.height
				local data = img:getData()
				local pixels = {}
				for x = 0, w - 1 do
					for y = 0, h - 1 do
						local i = y * w + x
						local v = data[i]
						local r, g, b, a = v.r, v.g, v.b, v.a
						pixels[("%s,%s"):format(x, y)] = {("&H%02X%02X%02X&"):format(b, g, r), ("&H%02X&"):format(255 - a)}
					end
				end
				return pixels
			end, --ke.image.to_pixels()
			
		},
		
		recall = {
			
			memory = {},
			
			remember = function(ref, value, cond)
				if cond == nil then
					if ke.recall.memory[ref] then return ke.recall.memory[ref] end
					cond = true
				elseif type(cond) == "function" then
					cond = cond()
				end
				if cond then
					ke.recall.memory[ref] = value
					return value
				end
				return ke.recall.memory[ref] or value
			end,
			
			reset = function(ref)
				if ref then
					ke.recall.memory[ref] = nil
				else
					ke.recall.memory = {}
				end
			end,
			
			retime = function(mode, add_start, add_end)
				add_start, add_end = ke.time.HMS_to_ms(add_start), ke.time.HMS_to_ms(add_end)
				local times, l, fx = ke.infofx.data.times, ke.infofx.data.l, ke.infofx.data.fx
				if mode == "line" then				-- mode[01]
					l.start_time = times.line.start_time + add_start
					l.end_time = times.line.end_time + add_end
				elseif mode == "preline" then		-- mode[02]
					l.start_time = times.line.start_time + add_start
					l.end_time = times.line.start_time + add_end
				elseif mode == "postline" then		-- mode[03]
					l.start_time = times.line.end_time + add_start
					l.end_time = times.line.end_time + add_end
				elseif mode == "word" then			-- mode[04]
					l.start_time = times.line.start_time + times.word.start_time + add_start
					l.end_time = times.line.start_time + times.word.end_time + add_end
				elseif mode == "preword" then		-- mode[05]
					l.start_time = times.line.start_time + times.word.start_time + add_start
					l.end_time = times.line.start_time + times.word.start_time + add_end
				elseif mode == "postword" then		-- mode[06]
					l.start_time = times.line.start_time + times.word.end_time + add_start
					l.end_time = times.line.start_time + times.word.end_time + add_end
				elseif mode == "syl" then			-- mode[07]
					l.start_time = times.line.start_time + times.syl.start_time + add_start
					l.end_time = times.line.start_time + times.syl.end_time + add_end
				elseif mode == "presyl" then		-- mode[08]
					l.start_time = times.line.start_time + times.syl.start_time + add_start
					l.end_time = times.line.start_time + times.syl.start_time + add_end
				elseif mode == "postsyl" then		-- mode[09]
					l.start_time = times.line.start_time + times.syl.end_time + add_start
					l.end_time = times.line.start_time + times.syl.end_time + add_end
				elseif mode == "char" then			-- mode[10]
					l.start_time = times.line.start_time + times.char.start_time + add_start
					l.end_time = times.line.start_time + times.char.end_time + add_end
				elseif mode == "prechar" then		-- mode[11]
					l.start_time = times.line.start_time + times.char.start_time + add_start
					l.end_time = times.line.start_time + times.char.start_time + add_end
				elseif mode == "postchar" then		-- mode[12]
					l.start_time = times.line.start_time + times.char.end_time + add_start
					l.end_time = times.line.start_time + times.char.end_time + add_end
				elseif mode == "start2word"	then	-- mode[13]
					l.start_time = times.line.start_time + add_start
					l.end_time = times.line.start_time + times.word.start_time + add_end
				elseif mode == "word2end" then		-- mode[14]
					l.start_time = times.line.start_time + times.word.end_time + add_start
					l.end_time = times.line.end_time + add_end
				elseif mode == "start2syl" then		-- mode[15]
					l.start_time = times.line.start_time + add_start
					l.end_time = times.line.start_time + times.syl.start_time + add_end
				elseif mode == "syl2end" then		-- mode[16]
					l.start_time = times.line.start_time + times.syl.end_time + add_start
					l.end_time = times.line.end_time + add_end
				elseif mode == "start2char"	then	-- mode[17]
					l.start_time = times.line.start_time + add_start
					l.end_time = times.line.start_time + times.char.start_time + add_end
				elseif mode == "char2end" then		-- mode[18]
					l.start_time = times.line.start_time + times.char.end_time + add_start
					l.end_time = times.line.end_time + add_end
				elseif mode == "linepct" then		-- mode[19]
					l.start_time = times.line.start_time + add_start * times.line.duration / 100
					l.end_time = times.line.start_time + add_end * times.line.duration / 100
				elseif mode == "wordpct" then		-- mode[20]
					l.start_time = times.line.start_time + times.word.start_time + add_start * times.word.duration / 100
					l.end_time = times.line.start_time + times.word.start_time + add_end * times.word.duration / 100
				elseif mode == "sylpct" then		-- mode[21]
					l.start_time = times.line.start_time + times.syl.start_time + add_start * times.syl.duration / 100
					l.end_time = times.line.start_time + times.syl.start_time + add_end * times.syl.duration / 100
				elseif mode == "charpct" then		-- mode[22]
					l.start_time = times.line.start_time + times.char.start_time + add_start * times.char.duration / 100
					l.end_time = times.line.start_time + times.char.start_time + add_end * times.char.duration / 100
				elseif mode == "set" or mode == "abs" then	-- mode[29]
					l.start_time = add_start
					l.end_time = add_end
				elseif mode == "startsyl2char" then	-- mode[23]
					l.start_time = times.line.start_time + times.syl.start_time + add_start
					l.end_time = times.line.start_time + times.char.start_time + add_end
				elseif mode == "startword2syl" then	-- mode[24]
					l.start_time = times.line.start_time + times.word.start_time + add_start
					l.end_time = times.line.start_time + times.syl.start_time + add_end
				elseif mode == "startword2char" then-- mode[25]
					l.start_time = times.line.start_time + times.word.start_time + add_start
					l.end_time = times.line.start_time + times.char.start_time + add_end
				elseif mode == "syl2endword" then	-- mode[26]
					l.start_time = times.line.start_time + times.syl.end_time + add_start
					l.end_time = times.line.start_time + times.word.end_time + add_end
				elseif mode == "char2endsyl" then	-- mode[27]
					l.start_time = times.line.start_time + times.char.end_time + add_start
					l.end_time = times.line.start_time + times.syl.end_time + add_end
				elseif mode == "char2endword" then	-- mode[28]
					l.start_time = times.line.start_time + times.char.end_time + add_start
					l.end_time = times.line.start_time + times.word.end_time + add_end
				else								-- mode["default"]
					l.start_time = times.line.start_time
					l.end_time = times.line.end_time
				end --retime("preword", 0, 0)
				fx.time_ini = l.start_time
				fx.time_fin = l.end_time
				fx.time_dur = fx.time_fin - fx.time_ini
				return ""
			end,
			
			maxloop = function(newmaxloop)
				local fx = ke.infofx.data.fx
				fx.maxj = math.abs(math.ceil(newmaxloop or 1))
				return ""
			end, --ke.recall.maxloop(3)
			
			rotcoor = function(x, y, angle, org)
				--auxiliary function for rotating cartesian coordinates
				local p = ke.shape.point.new(x, y):rotate(angle, org)
				return p.x, p.y
			end, --ke.recall.rotcoor
			
		},
		
		infofx = {
			
			data = {
				--saves relevant information about script and effect
			},
			
			sethead = function()
				local vars
				vars = {
					env = ke.table.setvalues(),
					setlibs = function(line)
						--create the four main ke2 libraries text
						local allsets = {
							["char"] = ke.config.text2char(line.text_raw, line.dur, line.style, line.left, line.top),
							["syl"]  = ke.config.text2syl(line.text_raw, line.dur, line.style, line.left, line.top),
							["word"] = ke.config.text2word(line.text_raw, line.dur, line.style, line.left, line.top),
							["line"] = {line},
						}
						return allsets
					end,
					
					setcswl = function(sets, fx, linei, orgline, index)
						local char = sets.char[fx.ci] or {1}
						local syl  = sets.syl[fx.si] or {1}
						local word = sets.word[fx.wi] or {1}
						local line = ke.table.copy(orgline)
						line.keeptgs = linei.keeptgs
						local keep = {char = char.keeptgs, syl = syl.keeptgs, word = word.keeptgs, line = line.keeptgs}
						char.n, syl.n, word.n, line.n = #sets.char, #sets.syl, #sets.word, #index
						local setn = {line = line.n, word = word.n, syl = syl.n, char = char.n}
						local fx__ = ke.infofx.data.fx__
						fx.n = setn[fx__.fx_type]
						ke.infofx.data.times = {
							char = {start_time = char.start_time, end_time = char.end_time},
							syl  = {start_time = syl.start_time,  end_time = syl.end_time},
							word = {start_time = word.start_time, end_time = word.end_time},
							line = {start_time = line.start_time, end_time = line.end_time}
						}
						return char, syl, word, line, keep[fx__.fx_type][fx__.fx_keept]
					end,
					
					setvarloop = function(char, syl, word, line, fx)
						local fx__ = ke.infofx.data.fx__
						--variables
						local svar = ("return function(char, syl, word, line, ke, fx, fx__) %s end"):format(fx__.fx_variable)
						local vars = ke.string.loadstr(fx__.fx_variable, {char = char, syl = syl, word = word, line = line, fx = fx})
						if pcall(loadstring(svar)) then
							loadstring(svar)()(char, syl, word, line, ke, fx, fx__)
						end
						--loop:
						local loop = {1}
						local sloop = ("return function(char, syl, word, line, ke, fx, fx__) return {%s} end"):format(fx__.fx_loop)
						if pcall(loadstring(sloop)) then
							loop = loadstring(sloop)()(char, syl, word, line, ke, fx, fx__)
						end
						local maxj = ke.table.iter(nil, function(i, v, s) return s * loop[i] end, {start = 1, i = {1, #loop}})
						ke.infofx.data.loop = loop
						return maxj, svar, vars
					end,
					
					setvariable = function(char, syl, word, line, svar, vars, j)
						local fx = ke.infofx.data.fx
						local fx__ = ke.infofx.data.fx__
						if pcall(loadstring(svar)) then
							loadstring(svar)()(char, syl, word, line, ke, fx, fx__)
						end
						local var = ke.table.hidden(vars() or {})
						var.char = remember("varchar", vars(), j == 1)
						if fx__.fx_type == "char" then
							var.syl  = remember("varcharsyl", vars(), char.is == 1 and j == 1)
							var.word = remember("varcharword", vars(), char.iw == 1 and j == 1)
							var.line = remember("varcharline", vars(), char.i == 1 and j == 1)
						else
							var.syl = remember("varsyl", vars(), j == 1)
						end
						if fx__.fx_type == "syl" then
							var.word = remember("varsylword", vars(), syl.iw == 1 and j == 1)
							var.line = remember("varsylline", vars(), syl.i == 1 and j == 1)
						else
							var.word = recall.varcharword or remember("varword", vars(), j == 1)
						end
						if fx__.fx_type == "word" then
							var.line = remember("varwordline", vars(), word.i == 1 and j == 1)
						else
							var.line = recall.varcharline or recall.varsylline or remember("varline", vars(), j == 1)
						end
						var.once = remember("varonce", vars())
						ke.infofx.data.fx.var = var
						return var
					end,
				}
				ke.infofx.data.xres, ke.infofx.data.yres = aegisub.video_size()
				ke.infofx.data.ratio = ke.math.round((ke.infofx.data.xres or 1280) / 1280, ROUND_NUM)
				local msa, msb = aegisub.ms_from_frame(1), aegisub.ms_from_frame(101)
				ke.infofx.data.frame_dur = msb and ke.math.round((msb - msa) / 100, ROUND_NUM) or 41.708
				vars.env.set({
					retime = ke.recall.retime,		--retime("word", 0, 0)
					maxloop = ke.recall.maxloop,	--maxloop(3)
					remember = ke.recall.remember,	--remember(ref, value[, cond])
					recall = ke.recall.memory,		--recall[ref]
					xres = ke.infofx.data.xres,
					yres = ke.infofx.data.yres,
					ratio = ke.infofx.data.ratio,
					frame_dur = ke.infofx.data.frame_dur,
					j = ke.infofx.data.j,
					maxj = ke.infofx.data.maxj,
					fxgroup = true,
				})
				return vars
			end,
			
			styles = function(lineinfo, fx__)
				--assign the style values ​​to the text library, and the corresponding styles from the shape library
				--text styles
				ke.text.bold	= lineinfo.bold			ke.text.underline	= lineinfo.underline
				ke.text.italic	= lineinfo.italic		ke.text.strikeout	= lineinfo.strikeout
				ke.text.align	= lineinfo.align		ke.text.fontsize	= lineinfo.fontsize
				ke.text.shadow	= lineinfo.shadow		ke.text.fontname	= lineinfo.fontname
				ke.text.spacing	= lineinfo.spacing		ke.text.margin_b	= lineinfo.margin_b
				ke.text.scale_x	= lineinfo.scale_x		ke.text.margin_l	= lineinfo.margin_l
				ke.text.scale_y	= lineinfo.scale_y		ke.text.margin_r	= lineinfo.margin_r
				ke.text.angle	= lineinfo.angle		ke.text.margin_t	= lineinfo.margin_t
				ke.text.outline	= lineinfo.outline		ke.text.margin_v	= lineinfo.margin_t
				ke.text.color1	= lineinfo.color1		ke.text.alpha1		= lineinfo.alpha1
				ke.text.color2	= lineinfo.color2		ke.text.alpha2		= lineinfo.alpha2
				ke.text.color3	= lineinfo.color3		ke.text.alpha3		= lineinfo.alpha3
				ke.text.color4	= lineinfo.color4		ke.text.alpha4		= lineinfo.alpha4
				ke.text.color	= ("\\1c%s\\3c%s\\4c%s"):format(ke.text.color1, ke.text.color3, ke.text.color4)
				ke.text.alpha	= ("\\1a%s\\3a%s\\4a%s"):format(ke.text.alpha1, ke.text.alpha3, ke.text.alpha4)
				ke.text.style	= ke.text.color .. ke.text.alpha
				--shape styles
				ke.shape.color1 = ke.color.ass(fx__.fx_color1)		ke.shape.alpha1 = ke.alpha.ass(fx__.fx_alpha1)
				ke.shape.color3 = ke.color.ass(fx__.fx_color3)		ke.shape.alpha3 = ke.alpha.ass(fx__.fx_alpha3)
				ke.shape.color4 = ke.color.ass(fx__.fx_color4)		ke.shape.alpha4 = ke.alpha.ass(fx__.fx_alpha4)
				ke.shape.color	= ("\\1c%s\\3c%s\\4c%s"):format(ke.shape.color1, ke.shape.color3, ke.shape.color4)
				ke.shape.alpha	= ("\\1a%s\\3a%s\\4a%s"):format(ke.shape.alpha1, ke.shape.alpha3, ke.shape.alpha4)
				ke.shape.style	= ke.shape.color .. ke.shape.alpha
			end, --ke.infofx.styles(data.l, fx__)
		},
		
		config = {
			
			window = {
				[01] = {x = 3;	y = 0;	height = 1;	width = 2; class = "label";		label = " [:: Primary Setting ::]"},
				[02] = {x = 2;	y = 1;	height = 1; width = 1; class = "label";		label = "                          Apply to Style:"},
				[03] = {x = 3;	y = 1;	height = 1; width = 4; class = "dropdown";	name = "line_style"; hint = "Selected Lines or Lines Styles to which you Apply the Effect.";	items = {};	value = "Selected Lines"},
				[04] = {x = 2;	y = 2;	height = 1; width = 1; class = "label";		label = "                       Selection Effect:"},
				[05] = {x = 3;	y = 2;	height = 1; width = 4; class = "dropdown";	name = "effect_mode"; hint = "Select the Effect Mode: leadin, hilight, leadout, shape or translation fx";	items = {"leadin fx", "hilight fx", "leadout fx", "shape fx", "translation fx", "install fx"};	value = "leadin fx"},
			},
			
			windowconfig = {
				[01] = {x = 0;	y = 0;	height = 1; width = 8; class = "label";		label = "lead-in[fx]: ABC New fx"},
				[02] = {x = 10;	y = 0;	height = 1; width = 2; class = "label";		label = "         Template Type [fx]:"},
				[03] = {x = 12;	y = 0;	height = 1; width = 2; class = "dropdown";	name = "fx_type"; items = {"line", "word", "syl", "char"}; value = "syl"},
				[04] = {x = 0;	y = 1;	height = 1; width = 2; class = "label";		label = "                       Line Start Time: "},
				[05] = {x = 2;	y = 1;	height = 1; width = 6; class = "textbox";	name = "fx_start"; text = "l.start_time"},
				[06] = {x = 8;	y = 1;	height = 1; width = 2; class = "label";		label = "                 layer // Align: "},
				[07] = {x = 10;	y = 1;	height = 1; width = 2; class = "textbox";	name = "fx_layer"; text = "0"},
				[08] = {x = 12;	y = 1;	height = 1; width = 2; class = "textbox";	name = "fx_align"; text = "5"},
				[09] = {x = 0;	y = 2;	height = 1; width = 2; class = "label";		label = "                        Line End Time: "},
				[10] = {x = 2;	y = 2;	height = 1; width = 6; class = "textbox";	name = "fx_end"; text = "l.end_time"},
				[11] = {x = 8;	y = 2;	height = 1; width = 2; class = "label";		label = "                                loop: "},
				[12] = {x = 10;	y = 2;	height = 1; width = 4; class = "textbox";	name = "fx_loop"; text = "1"},
				[13] = {x = 0;	y = 3;	height = 1; width = 2; class = "label";		label = "                              Return [fx]: "},
				[14] = {x = 2;	y = 3;	height = 4; width = 4; class = "textbox";	name = "fx_return"; text = "fx.text"},
				[15] = {x = 6;	y = 3;	height = 1; width = 2; class = "label";		label = "                           Pos \"x\": "},
				[16] = {x = 8;	y = 3;	height = 1; width = 6; class = "textbox";	name = "fx_posx"; text = "fx.center"},
				[17] = {x = 6;	y = 4;	height = 1; width = 2; class = "label";		label = "                           Pos \"y\": "},
				[18] = {x = 8;	y = 4;	height = 1; width = 6; class = "textbox";	name = "fx_posy"; text = "fx.middle"},
				[19] = {x = 0;	y = 5;	height = 1; width = 2; class = "checkbox";	name = "fx_modify"; label = "Modify or Return [fx]"; value = false},
				[20] = {x = 6;	y = 5;	height = 1; width = 2; class = "label";		label = "                  Times Move: "},
				[21] = {x = 8;	y = 5;	height = 1; width = 6; class = "textbox";	name = "fx_time"; text = ""},
				[22] = {x = 0;	y = 6;	height = 1; width = 1; class = "label";		label = "keeptags [fx]:"},
				[23] = {x = 1;	y = 6;	height = 1; width = 1; class = "dropdown";	name = "fx_keept"; items = {"line", "word", "syl"}; value = ""},
				[24] = {x = 2;	y = 7;	height = 1; width = 2; class = "label";		label = "   Shape Primary Color   "},
				[25] = {x = 4;	y = 7;	height = 1; width = 2; class = "label";		label = "    Shape Border Color    "},
				[26] = {x = 6;	y = 7;	height = 1; width = 2; class = "label";		label = "   Shape Shadow Color "},
				[27] = {x = 8;	y = 7;	height = 1; width = 2; class = "label";		label = " New [fx] Name:"},
				[28] = {x = 12;	y = 7;	height = 1; width = 2; class = "label";		label = " update: april 26th 2026"},
				[29] = {x = 2;	y = 8;	height = 2; width = 2; class = "color";		name = "fx_color1";	value = "#FFFFFF"},
				[30] = {x = 4;	y = 8;	height = 2; width = 2; class = "color";		name = "fx_color3";	value = "#B4B4B4"},
				[31] = {x = 6;	y = 8;	height = 2; width = 2; class = "color";		name = "fx_color4";	value = "#626262"},
				[32] = {x = 8;	y = 8;	height = 2; width = 6; class = "textbox";	name = "fx_namefx"; text = ""},
				[33] = {x = 0;	y = 10;	height = 1; width = 2; class = "label";		label = "New Eeffector 1.0"},
				[34] = {x = 2;	y = 10;	height = 1; width = 2; class = "intedit";	name = "fx_alpha1";	min = 0; max = 255;	value = "0"},
				[35] = {x = 4;	y = 10;	height = 1; width = 2; class = "intedit";	name = "fx_alpha3";	min = 0; max = 255;	value = "0"},
				[36] = {x = 6;	y = 10;	height = 1; width = 2; class = "intedit";	name = "fx_alpha4";	min = 0; max = 255;	value = "0"},
				[37] = {x = 8;	y = 10;	height = 1; width = 2; class = "checkbox";	name = "fx_printfx"; label = "Print Config [fx]"; value = false},
				[38] = {x = 10;	y = 10;	height = 1; width = 2; class = "label";		label = "       Template Folder [fx]:"},
				[39] = {x = 12;	y = 10;	height = 1; width = 2; class = "dropdown";	name = "fx_folder"; items = {"leadin fx", "hilight fx", "leadout fx", "shape fx", "translation fx"}; value = "leadin fx"},
				[40] = {x = 2;	y = 12;	height = 1; width = 2; class = "label";		label = " Variables [fx]:"},
				[41] = {x = 8;	y = 12;	height = 1; width = 2; class = "label";		label = " Add Tags [fx]:"},
				[42] = {x = 2;	y = 13;	height = 6; width = 6; class = "textbox";	name = "fx_variable"; text = ""},
				[43] = {x = 8;	y = 13;	height = 6; width = 6; class = "textbox";	name = "fx_addtags"; text = ""},
				[44] = {x = 0;	y = 16;	height = 1; width = 2; class = "checkbox";	name = "fx_reverse"; label = "Reverse [fx]"; value = false},
				[45] = {x = 0;	y = 17;	height = 1; width = 2; class = "checkbox";	name = "fx_noblank"; label = "Noblank [fx]"; value = true},
				[46] = {x = 0;	y = 18;	height = 1; width = 2; class = "checkbox";	name = "fx_vertical"; label = "Vertical Kanji [fx]"; value = false},
			},
			
			style = function(subtitles, selected_lines)
				local styles = {} --crea la tabla de los estilos para "Apply to Style:"
				for i = 1, #subtitles do
					if subtitles[i].class == "dialogue"
						and subtitles[i].effect ~= "Effector [fx]"
						and subtitles[i].effect ~= "fx"
						and not ke.table.inside(styles, subtitles[i].style) then
						styles[#styles + 1] = subtitles[i].style
					end
				end
				styles[#styles + 1] = #styles > 0 and  "All Lines" or nil
				styles[#styles + 1] = (selected_lines and #styles > 0) and "Selected Lines" or nil
				ke.config.window[3].items = styles --ingresa los estilos en la primera ventana
			end,
			
			apply = function(subtitles, selected_lines, sett, fx__)
				local index = {} --índices de las líneas fx
				if sett.line_style == "Selected Lines" then
					for _, v in ipairs(selected_lines) do
						if subtitles[v].class == "dialogue"
							and subtitles[v].effect ~= "Effector [fx]"
							and subtitles[v].effect ~= "fx" then
							index[#index + 1] = v 
						end
					end
				elseif sett.line_style == "All Lines" then
					for i = 1, #subtitles do
						if subtitles[i].class == "dialogue"
							and subtitles[i].effect ~= "Effector [fx]"
							and subtitles[i].effect ~= "fx" then
							index[#index + 1] = i
						end
					end
				else
					for i = 1, #subtitles do
						if sett.line_style == subtitles[i].style
							and subtitles[i].class  == "dialogue"
							and subtitles[i].effect ~= "Effector [fx]"
							and subtitles[i].effect ~= "fx" then
							index[#index + 1] = i
						end
					end
				end
				ke.infofx.data.fx__ = ke.table.copy(fx__)
				if fx__.fx_printfx then
					ke.config.savefx(fx__)
				else
					local meta, styles = karaskel.collect_head(subtitles)
					local linefx = ke.config.parseline(subtitles, meta, styles, index)
					ke.config.runfx(subtitles, meta, styles, index, linefx, sett, fx__)
				end
			end,
			
			macro = function(subtitles, selected_lines, active_line)
				ke.config.style(subtitles, #selected_lines > 0)
				local meta, styles = karaskel.collect_head(subtitles)
				local select_line_fx = selected_lines[1]
				local fxwin = ke.config.temp.get_namesfx()
				ke.config.temp.list_templates()
				local sett, box_res, fx__ = {}
				----------------
				::back_window1::
				----------------
				ke.config.window[05].items = {"leadin fx", "hilight fx", "leadout fx", "shape fx", "translation fx", "install fx"}
				if ke.config.window[07] then
					ke.config.window[05].items = {"leadin fx", "hilight fx", "leadout fx", "shape fx", "translation fx"}
				end
				repeat
					local buttoms = ke.config.window[07] and {"Apply Selection", "Cancel", "Back <"} or {"Apply Selection", "Cancel"}
					box_res, sett = aegisub.dialog.display(ke.config.window, buttoms, {ok = "Apply Selection", cancel = "Cancel"})
					if box_res == "Apply Selection" and sett.effect_mode == "install fx" then
						ke.config.window[06] = {x = 0; y = 5; height = 1; width = 2; class = "label"; label = " Install [fx]: "}
						ke.config.window[07] = {x = 0; y = 6; height = 4; width = 6; class = "textbox";	name = "install_fx"; text = ""}
						repeat
							box_res, sett = aegisub.dialog.display(ke.config.window, {"Install", "Cancel"}, {ok = "Install", cancel = "Cancel"})
							if box_res == "Install" then
								ke.config.installfx(sett.install_fx)
							end
							ke.config.window[06], ke.config.window[07] = nil
						until true
					else
						ke.config.window[05].items = {"leadin fx", "hilight fx", "leadout fx", "shape fx", "translation fx"}
						if ke.config.window[07] and sett.effect_mode then
							ke.config.window[07].value = sett.effect_name
						end
						ke.config.window[03].value = sett.line_style --save
						ke.config.window[05].value = sett.effect_mode
						local fxlist = fxwin(ke.config.window[05].value)
						if box_res == "Apply Selection" then
							ke.config.window[06] = {x = 0; y = 5; height = 1; width = 2; class = "label"; label = " Select [fx]: "}
							ke.config.window[07] = {x = 0; y = 6; height = 1; width = 6; class = "dropdown"; name = "effect_name";
								hint = "Select Karaoke Effect"; items = fxlist; value = sett.effect_name or fxlist[1]
							}
							repeat
								box_res, sett = aegisub.dialog.display(ke.config.window,
									{"Apply " .. sett.effect_mode, "Cancel", "Modify", "Back <"},
									{ok = "Apply " .. sett.effect_mode, cancel = "Cancel"}
								)
							until true
						end
						----------------
						::back_window2::
						----------------
						sett.effect_name = sett.effect_name or "ok"
						local preindex = sett.effect_name:match("%b[]") and sett.effect_name:match("%b[]"):sub(2, -2) or 1
						if ke.config.window[07] then
							local name = ke.config.window[07].value:gsub("%b[] ",""):gsub(" ", "_")		--name fx
							local mode = ke.config.window[05].value:gsub(" ", "")						--mode fx
							local indx = tonumber(preindex)												--index fx
							local windowfx = ke.config.temp.fx_to_table(templatesfx[mode][indx])			--table fx
							fx__ = ke.config.temp.loadprefx(windowfx)
							ke.config.window[07].value = sett.effect_name
							if box_res == "Back <" then
								ke.config.window[06], ke.config.window[07] = nil, nil
								goto back_window1
							end
							if box_res == "Apply " .. sett.effect_mode then
								ke.config.apply(subtitles, selected_lines, sett, fx__)
							end
							if box_res == "Modify" and sett.line_style ~= "" then
								windowfx[01].label = sett.effect_mode:gsub("fx", "[fx]: ") .. sett.effect_name:gsub("%b[] ","")
								windowfx[39].value = sett.effect_mode		--folder fx
								repeat
									-----------------
									::style_manager::
									-----------------
									box_res, fx__ = aegisub.dialog.display(windowfx,
										{"Apply " .. sett.effect_mode, "Cancel", "Style Colors", "Back <"},
										{ok = "Apply " .. sett.effect_mode, cancel = "Cancel"}
									)
									fx__.fx_name, fx__.fx_mode = name, mode
									ke.config.temp.fx_to_save(windowfx, fx__) --save configurations
									templatesfx[mode][indx] = ke.config.temp.fx_to_string(fx__)
									if box_res == "Style Colors" then
										local style_fx_shp = sett.line_style
										if sett.line_style == "Selected Lines" or sett.line_style == "All Lines" then
											style_fx_shp = subtitles[select_line_fx].style
										end
										windowfx[29].value = styles[style_fx_shp].color1
										windowfx[30].value = styles[style_fx_shp].color3
										windowfx[31].value = styles[style_fx_shp].color4
										windowfx[34].value = tonumber(styles[style_fx_shp].color1:match("(%x%x)"), 16)
										windowfx[35].value = tonumber(styles[style_fx_shp].color3:match("(%x%x)"), 16)
										windowfx[36].value = tonumber(styles[style_fx_shp].color4:match("(%x%x)"), 16)
										goto style_manager
									end
									if box_res == "Back <" then --ventana 1
										box_res, sett = aegisub.dialog.display(ke.config.window,
											{"Apply " .. sett.effect_mode, "Cancel", "Modify", "Back <"},
											{ok = "Apply " .. sett.effect_mode, cancel = "Cancel"}
										)
										goto back_window2
									end
								until true
								if box_res == "Apply " .. sett.effect_mode then
									ke.config.apply(subtitles, selected_lines, sett, fx__)
								end
							end
						end
					end
				until true
			end,
			
			karaoke_true = function(array)
				for i = 1, #array do
					if not array[i]:match("\\[kK]^*[fo]*%d+") then
						return false
					end
				end
				return true
			end,
			
			adjust_line = function(text)
				local auxtext, score = text, 1
				while score == 1 do
					auxtext = auxtext:gsub("(%b{})(%b{})",
						function(tag1, tag2)
							local result = tag1 .. tag2
							if not (tag1:match("\\[kK]^*[fo]*%d+") and tag2:match("\\[kK]^*[fo]*%d+")) then
								result = result:gsub("}{", "")
							end
							return result
						end
					)
					score = auxtext ~= text and 1 or 0
					text = auxtext
				end
				return auxtext
			end,
			
			to_word = function(linetext, linedur)
				local text = linetext:gsub("\\N", " ")
				text = ke.text.remove(text, "space_in_tags")
				text = ke.config.adjust_line(text)
				text = text:gsub("m%s+%-?%d[%.%-%d mlb]*", function(shp) shp = shp:gsub(" ", "€") return shp end)
				linedur = linedur or 10000
				local words = {}
				for w in text:gmatch("[%b{}]*[%S]*[\33-\47\58-\64]*[%s]*") do
					words[#words + 1] = w ~= "" and w:gsub("€", " ") or nil
				end
				words[1] = #words == 0 and ("{\\k%d}"):format(math.ceil(linedur / 10)) or words[1]
				return words
			end, --ke.config.to_word(l.text)
			
			text2word = function(linetext, linedur, linestyle, lineleft, linetop)
				linedur = linedur or 10000--fx.time_dur
				local words = ke.config.to_word(linetext, linedur)
				local words_dur, words_keep = {}, {word = {}, line = {}}
				if ke.config.karaoke_true(words) then
					for i = 1, #words do
						words_dur[i] = 0
						words_keep.word[i], words_keep.line[i] = "", i > 1 and words_keep.line[i - 1] or ""
						for tags in words[i]:gmatch("%b{}") do
							local kdur = tags:match("\\[kK]^*[fo]*(%d+)")
							words_dur[i] = words_dur[i] + kdur * 10
							tags = ke.string.delete(tags, {"\\pos%b()", "\\move%b()", "\\org%b()", "\\an%d", "\\[kK]^*[fo]*%d+"})
							words_keep.word[i] = words_keep.word[i] .. tags:sub(2, -2)
						end
						words_keep.line[i] = ke.string.delete(words_keep.line[i] .. words_keep.word[i], ke.text.keeptags, {protect = "\\t%b()", last = true})
					end
				else
					local textspc = ke.text.remove(linetext, "tags"):gsub(" ", "")
					local charn, wordspc = unicode.len(textspc)
					for i = 1, #words do
						words_keep.word[i], words_keep.line[i] = "", i > 1 and words_keep.line[i - 1] or ""
						for tags in words[i]:gmatch("%b{}") do
							tags = ke.string.delete(tags, {"\\pos%b()", "\\move%b()", "\\org%b()", "\\an%d", "\\[kK]^*[fo]*%d+"})
							words_keep.word[i] = words_keep.word[i] .. tags:sub(2, -2)
						end
						words_keep.line[i] = ke.string.delete(words_keep.line[i] .. words_keep.word[i], ke.text.keeptags, {protect = "\\t%b()", last = true})
						wordspc = ke.text.remove(words[i], "tags"):gsub(" ", "")
						words_dur[i] = ke.math.round(unicode.len(wordspc) * linedur / charn, ROUND_NUM)
					end
				end
				if linestyle then
					local word, start, kw = {}, 0, 1
					for k, w in ipairs(words) do
						local text_stripped = ke.text.remove(w, "tags")
						local text_first_spaces = text_stripped:match("(%s+).+") or ""
						local text_without_spaces = text_stripped:gsub("%s+", "")
						local width_first_spaces = aegisub.text_extents(linestyle, text_first_spaces)
						local width_without_spaces = aegisub.text_extents(linestyle, text_without_spaces)
						local width, height, descent, extlead = aegisub.text_extents(linestyle, text_stripped)
						word[kw] = {
							i			= kw,		ci			= kw,
							si			= kw,		wi			= kw,
							start_time	= start,
							end_time	= start + words_dur[k],
							duration	= words_dur[k],
							dur			= words_dur[k],
							text		= text_without_spaces,
							text_raw	= w,
							keeptgs		= {syl = words_keep.word[k], word = words_keep.word[k], line = words_keep.line[k]},
							-------------------------------------------------
							width	= width_without_spaces,					top		= linetop,
							left	= lineleft + width_first_spaces,		middle	= linetop + height / 2,
							center	= lineleft + width_without_spaces / 2,	bottom	= linetop + height,
							right	= lineleft + width_without_spaces,		descent	= descent,
							height	= height,								extlead	= extlead,
							-------------------------------------------------
						}
						kw = ke.infofx.data.fx__.fx_noblank and (text_without_spaces ~= "" and kw + 1 or kw) or kw + 1
						start = start + words_dur[k]
						lineleft = lineleft + width
					end
					return word
				end
				return words, words_dur, words_keep
			end,
			
			text2syl = function(linetext, linedur, linestyle, lineleft, linetop)
				linedur = linedur or 10000--fx.time_dur
				local words = ke.config.to_word(linetext, linedur)
				local syls, syls_dur, syl_wi, syl_iw, charn, syldur = {}, {}, {}, {}
				local textspc, wordspc = ke.text.remove(linetext, "tags"):gsub(" ", "")
				local syls_keep = {syl = {}, word = {}, line = {}}
				if ke.config.karaoke_true(words) then
					local i = 1
					for wi, w in pairs(words) do
						local words_keep_word = ""
						for tags in w:gmatch("%b{}") do
							tags = ke.string.delete(tags, {"\\pos%b()", "\\move%b()", "\\org%b()", "\\an%d", "\\[kK]^*[fo]*%d+"})
							words_keep_word = words_keep_word .. tags:sub(2, -2)
						end
						local si = 1
						for syl in w:gmatch("%b{}[\32-\122\124\126-\255]*") do
							syls_keep.syl[i] = ke.string.delete(syl:match("%b{}"), {"\\pos%b()", "\\move%b()", "\\org%b()", "\\an%d", "\\[kK]^*[fo]*%d+"}):sub(2, -2)
							syls_keep.word[i] = words_keep_word
							syls_keep.line[i] = i > 1 and syls_keep.line[i - 1] or ""
							syls_keep.line[i] = ke.string.delete(syls_keep.line[i] .. syls_keep.syl[i], ke.text.keeptags, {protect = "\\t%b()", last = true})
							table.insert(syls, syl)
							syldur = 0
							for kdur in syl:gmatch("\\[kK]^*[fo]*(%d+)") do
								syldur = syldur + kdur * 10
							end
							table.insert(syls_dur, syldur)
							table.insert(syl_wi, wi)
							table.insert(syl_iw, si)
							si, i = si + 1, i + 1
						end
					end
				else
					syls, charn, k = words, unicode.len(textspc), 1
					for i, w in pairs(words) do
						local words_keep_word = ""
						for tags in w:gmatch("%b{}") do
							tags = ke.string.delete(tags, {"\\pos%b()", "\\move%b()", "\\org%b()", "\\an%d", "\\[kK]^*[fo]*%d+"})
							words_keep_word = words_keep_word .. tags:sub(2, -2)
						end
						syls_keep.syl[k] = words_keep_word
						syls_keep.word[k] = words_keep_word
						syls_keep.line[k] = k > 1 and syls_keep.line[k - 1] or ""
						syls_keep.line[k] = ke.string.delete(syls_keep.line[k] .. syls_keep.syl[k], ke.text.keeptags, {protect = "\\t%b()", last = true})
						wordspc = ke.text.remove(w, "tags"):gsub(" ", "")
						syls_dur[i] = ke.math.round(unicode.len(wordspc) * linedur / charn, 3)
						table.insert(syl_wi, i)
						table.insert(syl_iw, i)
						k = k + 1
					end
				end
				if linestyle then
					local syl, start, ks = {}, 0, 1
					for k, s in ipairs(syls) do
						local text_stripped = ke.text.remove(s, "tags")
						local text_first_spaces = text_stripped:match("(%s+).+") or ""
						local text_without_spaces = text_stripped:gsub("%s+", "")
						local width_first_spaces = aegisub.text_extents(linestyle, text_first_spaces)
						local width_without_spaces = aegisub.text_extents(linestyle, text_without_spaces)
						local width, height, descent, extlead = aegisub.text_extents(linestyle, text_stripped)
						syl[ks] = {
							i			= ks,
							ci			= ks,
							si			= ks,
							wi			= syl_wi[k],
							iw			= syl_iw[k],
							start_time	= start,
							end_time	= start + syls_dur[k],
							duration	= syls_dur[k],
							dur			= syls_dur[k],
							text		= text_without_spaces,
							text_raw	= s,
							tags		= s:match("%b{}") or "",
							keeptgs		= {syl = syls_keep.syl[k], word = syls_keep.word[k], line = syls_keep.line[k]},
							-------------------------------------------------
							width	= width_without_spaces,					top		= linetop,
							left	= lineleft + width_first_spaces,		middle	= linetop + height / 2,
							center	= lineleft + width_without_spaces / 2,	bottom	= linetop + height,
							right	= lineleft + width_without_spaces,		descent	= descent,
							height	= height,								extlead	= extlead,
							-------------------------------------------------
						}
						ks = ke.infofx.data.fx__.fx_noblank and (text_without_spaces ~= "" and ks + 1 or ks) or ks + 1
						start = start + syls_dur[k]
						lineleft = lineleft + width
					end
					return syl
				end
				return syls, syls_dur, syls_keep
			end,
			
			text2char = function(linetext, linedur, linestyle, lineleft, linetop)
				linedur = linedur or 10000--fx.time_dur
				local words = ke.config.to_word(linetext, linedur)
				local sylstp, syldur, sylspc, charsyl
				local charn, charn_dur = {}, {}
				local char_wi, char_si, char_is, char_iw = {}, {}, {}, {}
				local chars_keep = {syl = {}, word = {}, line = {}}
				if ke.config.karaoke_true(words) then
					local si, i = 1, 1
					for wi, w in pairs(words) do
						local words_keep_word = ""
						for tags in w:gmatch("%b{}") do
							tags = ke.string.delete(tags, {"\\pos%b()", "\\move%b()", "\\org%b()", "\\an%d", "\\[kK]^*[fo]*%d+"})
							words_keep_word = words_keep_word .. tags:sub(2, -2)
						end
						local wk = 1
						for syl in w:gmatch("%b{}[\32-\122\124\126-\255]*") do
							chars_keep.syl[i] = ke.string.delete(syl:match("%b{}"), {"\\pos%b()", "\\move%b()", "\\org%b()", "\\an%d", "\\[kK]^*[fo]*%d+"}):sub(2, -2)
							chars_keep.word[i] = words_keep_word
							chars_keep.line[i] = i > 1 and chars_keep.line[i - 1] or ""
							chars_keep.line[i] = ke.string.delete(chars_keep.line[i] .. chars_keep.syl[i], ke.text.keeptags, {protect = "\\t%b()", last = true})
							syldur, sylstp = 0, ke.text.remove(syl, "tags")
							for kdur in syl:gmatch("\\[kK]^*[fo]*(%d+)") do
								syldur = syldur + kdur * 10
							end
							local sk = 1
							if sylstp == "" then
								table.insert(charn, "")
								table.insert(charn_dur, syldur)
								table.insert(char_wi, wi)	table.insert(char_si, si)
								table.insert(char_is, sk)	table.insert(char_iw, wk)
							else
								sylspc = sylstp:gsub(" ", "")
								charsyl = unicode.len(sylspc) == 0 and 1 or unicode.len(sylspc)
								for c in unicode.chars(sylstp) do
									table.insert(charn, c)
									table.insert(charn_dur, c == " " and 0 or ke.math.round(syldur / charsyl, 3))
									table.insert(char_wi, wi)	table.insert(char_si, si)
									table.insert(char_is, sk)	table.insert(char_iw, wk)
									sk = sk + 1
									wk = wk + 1
								end
							end
							si, i = si + 1, i + 1
						end
					end
				else
					local textunspaces = ke.text.remove(linetext, "tags"):gsub(" ", "")
					local charline, swi = unicode.len(textunspaces), 1
					for i, w in pairs(words) do
						local i_word = 1
						for c in unicode.chars(ke.text.remove(w, "tags")) do
							table.insert(charn, c)
							table.insert(charn_dur, c == " " and 0 or ke.math.round(linedur / charline, ROUND_NUM))
							table.insert(char_wi, swi)		table.insert(char_si, swi)
							table.insert(char_is, i_word)	table.insert(char_iw, i_word)
							swi = swi + (c == " " and 1 or 0)
							i_word = i_word + 1
						end
						local words_keep_word = ""
						for tags in w:gmatch("%b{}") do
							tags = ke.string.delete(tags, {"\\pos%b()", "\\move%b()", "\\org%b()", "\\an%d", "\\[kK]^*[fo]*%d+"})
							words_keep_word = words_keep_word .. tags:sub(2, -2)
						end
						chars_keep.syl[i] = words_keep_word
						chars_keep.word[i] = words_keep_word
						chars_keep.line[i] = i > 1 and chars_keep.line[i - 1] or ""
						chars_keep.line[i] = ke.string.delete(chars_keep.line[i] .. chars_keep.syl[i], ke.text.keeptags, {protect = "\\t%b()", last = true})
					end
				end
				if linestyle then
					local chars, start, kc = {}, 0, 1
					for k, c in ipairs(charn) do
						local width, height, descent, extlead = aegisub.text_extents(linestyle, c)
						chars[kc] = {
							i			= kc,
							ci			= kc,
							si			= char_si[k],
							wi			= char_wi[k],
							is			= char_is[k],
							iw			= char_iw[k],
							start_time	= start,
							end_time	= start + charn_dur[k],
							duration	= charn_dur[k],
							dur			= charn_dur[k],
							text		= c,
							text_raw	= c,
							keeptgs		= {syl = chars_keep.syl[k], word = chars_keep.word[k], line = chars_keep.line[k]},
							-------------------------------------------------
							width	= width,				top		= linetop,
							left	= lineleft,				middle	= linetop + height / 2,
							center	= lineleft + width / 2,	bottom	= linetop + height,
							right	= lineleft + width,		descent	= descent,
							height	= height,				extlead	= extlead,
							-------------------------------------------------
						}
						kc = ke.infofx.data.fx__.fx_noblank and ((c ~= " " and c ~= "") and kc + 1 or kc) or kc + 1
						start = start + charn_dur[k]
						lineleft = lineleft + width
					end
					return chars
				end
				return charn, charn_dur
			end,
			
			parseline = function(subtitles, meta, styles, index)
				local xres = meta.res_x or 1280
				local yres = meta.res_y or 720
				local DefaultKE = {
					["raw"] = "Style: DefaultKE,Arial,25,&H00FFFFFF,&H000000FF,&H00000000,&H00000000,0,0,0,0,100,100,0,0,1,2,2,2,20,20,20,1";
					["color1"] = "&H00FFFFFF&";		["color2"] = "&H000000FF&";		["color3"] = "&H00000000&";		["color4"] = "&H00000000&";
					["class"]		= "style";		["name"]		= "DefaultKE";	["fontname"]	= "Arial";		["section"]		= "[V4+ Styles]";
					["bold"]		= false;		["italic"]		= false;		["underline"]	= false;		["strikeout"]	= false;
					["scale_x"]		= 100;			["scale_y"] 	= 100;			["outline"]		= 2;			["shadow"]		= 2;
					["spacing"]		= 0;			["fontsize"]	= 25;			["angle"]		= 0;			["borderstyle"]	= 1;
					["alignment"]	= 2;			["align"]		= 2;			["margin_l"]	= 20;			["margin_r"]	= 20;
					["margin_v"]	= 20;			["margin_b"]	= 20;			["margin_t"]	= 20;			["encoding"]	= 1;
					["relative_to"]	= 2
				}
				local linefx = {}
				for i, v in ipairs(index) do
					local line = subtitles[v]
					line.text_stripped = ke.text.remove(line.text, "tags")
					line.text = ke.text.remove(line.text, "space_in_tags")
					--line.text = line.text:gsub("(%b{})(%s+)([\32-\122\124\126-\255]*)", "%2%1%3")
					local style = styles[line.style] or DefaultKE
					local width, height, descent, extlead = aegisub.text_extents(style, line.text_stripped)
					local psx, psy = line.text:match("\\pos%((%-?%d[%.%d]*),(%-?%d[%.%d]*)%)")
					local options_lft_line = {
						[1] = psx or style.margin_l,
						[2] = psx and psx - width / 2 or (xres + style.margin_l - style.margin_r - width) / 2,
						[3] = psx and psx + width / 2 or xres - style.margin_r - width
					}
					local options_top_line = {
						[1] = psy and psy - height or yres - style.margin_b - height,
						[2] = psy and psy - height / 2 or (yres + style.margin_t - style.margin_b - height) / 2,
						[3] = psy or style.margin_t
					}
					local left = options_lft_line[(style.align - 1) % 3 + 1]
					local ltop = options_top_line[math.ceil(style.align / 3)]
					local keeptg = ""
					for tags in line.text:gmatch("%b{}") do
						tags = ke.string.delete(tags, {"\\pos%b()", "\\move%b()", "\\org%b()", "\\an%d", "\\[kK]^*[fo]*%d+"})
						keeptg = keeptg .. tags:sub(2, -2)
					end
					local lnfx = {
						i	= i,	si	= i,	is	= i,
						ci	= i,	wi	= i,	iw	= i,
						----------------------------------------------------------
						start_time	= line.start_time,
						end_time	= line.end_time,
						duration	= line.end_time - line.start_time,
						dur			= line.end_time - line.start_time,
						text_raw	= line.text,
						text		= line.text_stripped,
						keeptgs		= {syl = keeptg, word = keeptg, line = keeptg}, --keeptags
						----------------------------------------------------------
						width	= width,			top		= ltop,
						left	= left,				middle	= ltop + height / 2,
						center	= left + width / 2,	bottom	= ltop + height,
						right	= left + width,		descent	= descent,
						height	= height,			extlead	= extlead,
						----------------------------------------------------------
						style	= style,
						bold	= style.bold,		underline	= style.underline,
						italic	= style.italic,		strikeout	= style.strikeout,
						align	= style.align,		fontsize	= style.fontsize,
						shadow	= style.shadow,		fontname	= style.fontname,
						spacing	= style.spacing,	margin_b	= style.margin_b,
						scale_x	= style.scale_x,	margin_l	= style.margin_l,
						scale_y	= style.scale_y,	margin_r	= style.margin_r,
						angle	= style.angle,		margin_t	= style.margin_t,
						outline	= style.outline,	margin_v	= style.margin_t,
						----------------------------------------------------------
						color1 = "&H" .. style.color1:match("%x%x(%x%x%x%x%x%x)") .. "&",
						color2 = "&H" .. style.color2:match("%x%x(%x%x%x%x%x%x)") .. "&",
						color3 = "&H" .. style.color3:match("%x%x(%x%x%x%x%x%x)") .. "&",
						color4 = "&H" .. style.color4:match("%x%x(%x%x%x%x%x%x)") .. "&",
						alpha1 = "&H" .. style.color1:match("(%x%x)%x%x%x%x%x%x") .. "&",
						alpha2 = "&H" .. style.color2:match("(%x%x)%x%x%x%x%x%x") .. "&",
						alpha3 = "&H" .. style.color3:match("(%x%x)%x%x%x%x%x%x") .. "&",
						alpha4 = "&H" .. style.color4:match("(%x%x)%x%x%x%x%x%x") .. "&",
						----------------------------------------------------------
						pretime = i == 1 and 300 or line.start_time - linefx[i - 1].end_time,
						posttime = linefx[i + 1] and linefx[i + 1].start_time - line.end_time or 300,
					}
					local org = {x = {lnfx.left, lnfx.center, lnfx.right}, y = {lnfx.bottom, lnfx.middle, lnfx.top}}
					lnfx.org = ke.shape.point.new(org.x[(style.align - 1) % 3 + 1], org.y[math.ceil(style.align / 3)])
					table.insert(linefx, lnfx)
				end
				return linefx
			end,
			
			temp = {
				list_templates = function()
					local ke_path = debug.getinfo(1, "S").source
					local folfer = ke_path:match("(.*/)") or ke_path:match("(.*\\)")
					local path = folfer .. "newkara_fxlist.lua"
					for l in io.lines(path) do
						local newfx_config, newfx_name = l:match("((%w+[_%w%d]*)%s*=%s*%b{})")
						if newfx_name then
							local typefx = newfx_config:match("{%s*\"(%w+[_%w%d]*)\"")
							table.insert(templatesfx[typefx], newfx_config)
						end
					end
				end,
				
				get_namesfx = function()
					local ke_path = debug.getinfo(1, "S").source
					local folfer = ke_path:match("(.*/)") or ke_path:match("(.*\\)")
					local path = folfer .. "newkara_fxlist.lua"
					local templates = {leadinfx = {}, hilightfx = {}, leadoutfx = {}, shapefx = {}, translationfx = {}}
					for l in io.lines(path) do
						local newfx_config, newfx_name = l:match("((%w+[_%w%d]*)%s*=%s*%b{})")
						if newfx_name then
							local typefx = newfx_config:match("{%s*\"(%w+[_%w%d]*)\"")
							table.insert(templates[typefx], newfx_config)
						end
					end
					return function(mode)
						mode = mode:gsub(" ", "")
						local names, numlist = {}, ("%%.%sd"):format(tostring(#templates[mode]):len())
						for i, xfx in ipairs(templates[mode]) do
							local indx = (numlist):format(i)
							local name = xfx:match("(%w+[_%w%d]*)%s*=%s*")
							names[i] = ("[%s] %s"):format(indx, name:gsub("_", " "))
						end
						return names --index and name: "[1] demo leadin33"
					end
				end,
				
				fx_to_table = function(name)
					local selectfx = name:match("%b{}")
					local getfx, _ = load(("return %s"):format(selectfx), "loadfx", "t")
					local _, configs = pcall(getfx)
					local guifx = ke.table.copy(ke.config.windowconfig)
					guifx[01].label	= configs[02] --[[name fx]]
					guifx[03].value	= configs[03] --[[template type]]	guifx[05].text	= configs[04] --[[line start time]]
					guifx[10].text	= configs[05] --[[line end time]]	guifx[07].text	= configs[06] --[[layer]]
					guifx[08].text	= configs[07] --[[aling]]			guifx[12].text	= configs[08] --[[loop]]
					guifx[14].text	= configs[09] --[[return]]			guifx[16].text	= configs[10] --[[pos x]]
					guifx[18].text	= configs[11] --[[pos y]]			guifx[21].text	= configs[12] --[[time move]]
					guifx[29].value	= configs[13] --[[shape color 1]]	guifx[30].value	= configs[14] --[[shape color 3]]
					guifx[31].value	= configs[15] --[[shape color 4]]	guifx[34].value	= configs[16] --[[shape alpha 1]]
					guifx[35].value	= configs[17] --[[shape alpha 3]]	guifx[36].value	= configs[18] --[[shape alpha 4]]
					guifx[42].text	= configs[19] --[[variables]]		guifx[43].text	= configs[20] --[[add tags]]
					guifx[44].value	= configs[21] --[[reverse fx]]		guifx[45].value	= configs[22] --[[noblank]]
					guifx[46].value	= configs[23] --[[vertical kanji]]
					return guifx
				end, --templates[mode][index]
				
				fx_to_string = function(array)
					local function str_op(array, quotation)
						for k, str in ipairs(array) do
							if type(str) == "string" then
								str = str:gsub("\\", "\\\\"):gsub("\"","\\%1"):gsub("\n", "\\n")--:gsub(" +", " ")
								str = quotation and "\"" .. str .. "\"" or str
							end
							array[k] = str
						end
						return table.unpack(array)
					end
					local numcode = ke.string.disorder(tostring(os.time()):sub(-7, -1))
					array.fx_folder = array.fx_folder:gsub(" ", "")
					array.fx_namefx = array.fx_namefx == "" and array.fx_folder .. numcode or array.fx_namefx:gsub(" ", "_")
					local values = {
						array.fx_folder, array.fx_namefx, array.fx_type, array.fx_start, array.fx_end, array.fx_layer, array.fx_align, array.fx_loop,
						array.fx_return, array.fx_posx, array.fx_posy, array.fx_time, array.fx_color1, array.fx_color3, array.fx_color4, array.fx_alpha1,
						array.fx_alpha3, array.fx_alpha4, array.fx_variable, array.fx_addtags, array.fx_reverse, array.fx_noblank, array.fx_vertical
					}
					local fxstring = ("{%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s}"):format(str_op(values, true))
					fxstring = ("	--[[%s]]	%s = %s"):format(os.date("%d/%m/%y %H:%M"), array.fx_namefx, fxstring)
					return fxstring
				end,
				
				fx_to_save = function(windowfx, fx__)
					--save configurations
					windowfx[03].value	= fx__.fx_type		windowfx[05].text	= fx__.fx_start		windowfx[10].text	= fx__.fx_end
					windowfx[07].text	= fx__.fx_layer		windowfx[08].text	= fx__.fx_align		windowfx[12].text	= fx__.fx_loop
					windowfx[14].text	= fx__.fx_return	windowfx[16].text	= fx__.fx_posx		windowfx[18].text	= fx__.fx_posy
					windowfx[21].text	= fx__.fx_time		windowfx[29].value	= fx__.fx_color1	windowfx[30].value	= fx__.fx_color3
					windowfx[31].value	= fx__.fx_color4	windowfx[34].value	= fx__.fx_alpha1	windowfx[35].value	= fx__.fx_alpha3
					windowfx[36].value	= fx__.fx_alpha4	windowfx[42].text	= fx__.fx_variable	windowfx[43].text	= fx__.fx_addtags
					windowfx[44].value	= fx__.fx_reverse	windowfx[45].value	= fx__.fx_noblank	windowfx[46].value	= fx__.fx_vertical
					windowfx[19].value	= fx__.fx_modify	windowfx[23].value	= fx__.fx_keept		windowfx[32].text	= fx__.fx_namefx
					windowfx[39].value	= fx__.fx_folder
				end,
				
				loadprefx = function(guifx)
					return {
						fx_type		= guifx[03].value,	fx_start	= guifx[05].text,	fx_end		= guifx[10].text,
						fx_layer	= guifx[07].text,	fx_align	= guifx[08].text,	fx_loop		= guifx[12].text,
						fx_return	= guifx[14].text,	fx_posx		= guifx[16].text,	fx_posy		= guifx[18].text,
						fx_time		= guifx[21].text,	fx_color1	= guifx[29].value,	fx_color3	= guifx[30].value,
						fx_color4	= guifx[31].value,	fx_alpha1	= guifx[34].value,	fx_alpha3	= guifx[35].value,
						fx_alpha4	= guifx[36].value,	fx_variable	= guifx[42].text,	fx_addtags	= guifx[43].text,
						fx_reverse	= guifx[44].value,	fx_noblank	= guifx[45].value,	fx_vertical	= guifx[46].value,
						fx_modify	= guifx[19].value,	fx_keept	= guifx[23].value,	fx_namefx	= guifx[32].text,
						fx_folder	= guifx[39].value
					}
				end,
				
				valbox = function(meta, char, syl, word, line, l, fx, var, j, maxj)
					local fx__ = ke.infofx.data.fx__
					local setting = {ke, fx__, meta, char, syl, word, line, l, fx, var, j, maxj}
					local tovalue = "return function(ke, fx__, meta, char, syl, word, line, l, fx, var, j, maxj) return %s end"
					local totable = "return function(ke, fx__, meta, char, syl, word, line, l, fx, var, j, maxj) return {%s} end"
					---------------------------------------
					local vals = {}
					--start and end times:
					fx__.fx_start = fx__.fx_start:gsub("(%d+%:%d+%:%d+%.%d+)", function(HMS) return tostring(ke.time.HMS_to_ms(HMS)) end)
					fx__.fx_end = fx__.fx_end:gsub("(%d+%:%d+%:%d+%.%d+)", function(HMS) return tostring(ke.time.HMS_to_ms(HMS)) end)
					fx__.fx_start, fx__.fx_end = ke.tag.tonumber(fx__.fx_start), ke.tag.tonumber(fx__.fx_end)
					local start_t = loadstring(totable:format(fx__.fx_start))()
					local end_t = loadstring(totable:format(fx__.fx_end))()
					vals.start_time = start_t(table.unpack(setting))[1] or line.start_time
					vals.end_time = end_t(table.unpack(setting))[1] or line.end_time
					vals.dur = vals.end_time - vals.start_time
					---------------------------------------
					--align:
					fx__.fx_align = ke.tag.tonumber(fx__.fx_align)
					local align = loadstring(tovalue:format(fx__.fx_align))()
					vals.align = "\\an" .. (align(table.unpack(setting)) or 5)
					---------------------------------------
					--position, move and time move:
					fx__.fx_posx = ke.tag.tonumber(fx__.fx_posx)
					fx__.fx_posy = ke.tag.tonumber(fx__.fx_posy)
					fx__.fx_time = ke.tag.tonumber(fx__.fx_time)
					local pos_x = loadstring(totable:format(fx__.fx_posx))()
					local pos_y = loadstring(totable:format(fx__.fx_posy))()
					local times = loadstring(totable:format(fx__.fx_time))()
					times = times(table.unpack(setting))
					pos_x = pos_x(table.unpack(setting))
					pos_y = pos_y(table.unpack(setting))
					vals.t1, vals.t2 = times[1] or 0, times[2] or vals.dur
					vals.x, vals.y = pos_x[1] or fx.center, pos_y[1] or fx.middle
					local pos_knjx, pos_knjy = vals.x, vals.y
					local pos_rever_x = fx__.fx_reverse and l.right + l.left - 2 * fx.center or 0
					local xres = aegisub.video_size()
					if fx__.fx_vertical then
						pos_rever_x, rev = 0, fx__.fx_reverse and -1 or 1
						local opx = {
							[1] = l.margin_l + l.height / 2,
							[2] = l.margin_l + (xres - l.margin_l - l.margin_r) / 2,
							[3] = xres - l.margin_r - l.height / 2,
						}
						local opy = {
							[1] = l.middle + l.height * rev * (0.9 * (fx.i - (rev == -1 and 1 or fx.n))),
							[2] = l.middle + l.height * rev * (0.9 * (fx.i - fx.n / 2 - 1) + 0.45),
							[3] = l.middle + l.height * rev * (0.9 * (fx.i - (rev == -1 and fx.n or 1))),
						}
						pos_knjx = opx[(tonumber(vals.align:match("%d")) - 1) % 3 + 1]
						pos_knjy = opy[math.ceil(tonumber(vals.align:match("%d")) / 3)]
					end
					vals.x, vals.y = pos_knjx + pos_rever_x, pos_knjy
					vals.x2, vals.y2 = pos_x[2] or nil, pos_y[2] or nil
					if vals.x2 or vals.y2 then
						vals.x2, vals.y2 = vals.x2 or vals.x, vals.y2 or vals.y
						vals.x2, vals.y2 = ke.recall.rotcoor(vals.x2, vals.y2, l.styleref.angle, ke.infofx.data.l.org)
					end
					vals.x, vals.y = ke.recall.rotcoor(vals.x, vals.y, l.styleref.angle, ke.infofx.data.l.org)
					vals.x1, vals.y1 = vals.x, vals.y
					vals.pos = ("\\pos(%s,%s)"):format(vals.x, vals.y)
					vals.pos = vals.x2 and ("\\move(%s,%s,%s,%s,%s,%s)"):format(vals.x1, vals.y1, vals.x2, vals.y2, vals.t1, vals.t2) or vals.pos
					---------------------------------------
					--layer:
					fx__.fx_layer = ke.tag.tonumber(fx__.fx_layer)
					local layer = loadstring(tovalue:format(fx__.fx_layer))()
					vals.layer = layer(table.unpack(setting)) or line.layer
					---------------------------------------
					for k, v in pairs(vals) do
						if type(v) == "string" then
							vals[k] = ke.tag.dark(v)
						end
					end
					---------------------------------------
					ke.infofx.data.fx.time_dur = vals.dur
					ke.infofx.data.fx.time_ini, ke.infofx.data.fx.time_fin = vals.start_time, vals.end_time
					ke.infofx.data.fx.align = vals.align
					ke.infofx.data.fx.x, ke.infofx.data.fx.x1, ke.infofx.data.fx.x2 = vals.x, vals.x1, vals.x1
					ke.infofx.data.fx.y, ke.infofx.data.fx.y1, ke.infofx.data.fx.y2 = vals.y, vals.y1, vals.y1
					ke.infofx.data.fx.t1, ke.infofx.data.fx.t2 = vals.t1, vals.t2
					ke.infofx.data.fx.layer = vals.layer
					---------------------------------------
					--add tags:
					vals.add_tags = ""
					fx__.fx_addtags = ke.tag.tonumber(fx__.fx_addtags)
					local tags = loadstring(totable:format(fx__.fx_addtags))()
					tags = tags(table.unpack(setting))
					if type(tags) == "table" and #tags > 0 then
						for _, v in pairs(tags) do
							vals.add_tags = vals.add_tags .. v
						end
					end
					vals.add_tags = ke.tag.dark(vals.add_tags)
					vals.align = vals.add_tags:match("\\an%d") and "" or vals.align
					vals.pos = vals.add_tags:match("\\[mp]^*o[sv]^*e?") and "" or vals.pos
					ke.infofx.data.fx.add_tags = vals.add_tags
					---------------------------------------
					--return:
					fx__.fx_return = ke.tag.tonumber(fx__.fx_return)
					local returnfx = loadstring(totable:format(fx__.fx_return))()
					vals.returnfx = returnfx(table.unpack(setting))[1] or fx.text
					if type(vals.returnfx) == "number" then
						vals.returnfx = tostring(vals.returnfx)
					end
					if type(vals.returnfx) == "table" then
						vals.returnfx = (vals.returnfx.__name and vals.returnfx.__name == "shape") and vals.returnfx.code or ke.table.view(vals.returnfx)
					end
					if vals.returnfx:gsub("%b{}", ""):match("m%s+%-?%d[%.%-%d mlb]*") then
						local shp = vals.returnfx:gsub("%b{}", ""):match("m%s+%-?%d[%.%-%d mlb]*")
						if shp ~= "m 0 0 m 0 100 " and shp ~= "m 0 0 m 100 100 "
							and not vals.returnfx:match("bars m") then
							local p_in_return = vals.returnfx:match("\\p%d")
							if p_in_return then
								vals.returnfx = vals.returnfx:gsub("\\p%d", "")
								vals.add_tags = vals.add_tags:gsub("\\p%d", "") .. p_in_return
							else
								local tags_p = ke.table.new(vals.add_tags:gmatch("\\p%d"))
								local p_in_tags = (tags_p.n > 0 and tags_p[tags_p.n] ~= "\\p0") and "" or "\\p1"
								vals.add_tags = vals.add_tags .. p_in_tags
							end
							local tags = ke.tag.array(vals.add_tags)
							local stag = ke.table.new({"\\1a", "\\3a", "\\4a", "\\1c", "\\3c", "\\4c"})
							local shape_style = {
								["\\1c"] = ke.color.ass(fx__.fx_color1),	["\\1a"] = ke.alpha.ass(fx__.fx_alpha1),
								["\\3c"] = ke.color.ass(fx__.fx_color3),	["\\3a"] = ke.alpha.ass(fx__.fx_alpha3),
								["\\4c"] = ke.color.ass(fx__.fx_color4),	["\\4a"] = ke.alpha.ass(fx__.fx_alpha4)
							}
							for i, v in ipairs(tags) do
								if stag:inside(v.tag) then
									shape_style[v.tag] = nil
								end
							end
							local shptags = ""
							for k, v in pairs(shape_style) do
								shptags = shptags .. k .. v
							end
							vals.add_tags = shptags .. vals.add_tags
						end
					end
					vals.returnfx = ke.tag.dark(vals.returnfx:gsub("bars m", "m")):gsub("}{", "")
					vals.align = vals.returnfx:match("\\an%d") and "" or vals.align
					vals.pos = vals.returnfx:match("\\[mp]^*o[sv]^*e?") and "" or vals.pos
					ke.infofx.data.fx.returnfx = vals.returnfx
					---------------------------------------
					ke.table.insert(fx, vals, false, true)
				end,
			},
			
			savefx = function(array)
				local newfx = ke.config.temp.fx_to_string(array)
				local ke_path = debug.getinfo(1, "S").source
				local folfer = ke_path:match("(.*/)") or ke_path:match("(.*\\)")
				local path = folfer .. "newkara_fxlist.lua"
				local fxfile = io.open(path, "a+")
				--fxfile = fxfile or io.open(aegisub.decode_path( "?data" ) .. "\\automation\\autoload\\kelibs\\newkara_fxlist.lua", "w")
				if fxfile then
					fxfile:write(newfx .. "\n")
					fxfile:close()
				end
				aegisub.debug.out("The new effect has been saved successfully, you must reload the script Kara so you can see it in the list effects.")
			end,
			
			demo_upgrade = function()
				local ke_path = debug.getinfo(1, "S").source
				local folfer = ke_path:match("(.*/)") or ke_path:match("(.*\\)")
				local path = folfer .. "file_functions.lua"
				local f = assert(io.open(path, "r"))
				local content = f:read("*a")
				f:close()
				return content
			end, --ke.config.dem()
			
			installfx = function(stringfx)
				stringfx = stringfx:match("%b{}")
				local libraryfx, namefx = stringfx:match('(%b"")%s*,%s*(%b"")')
				libraryfx, namefx = libraryfx:sub(2, -2), namefx:sub(2, -2)
				local newfx = ("	--[[%s %s]]	%s = %s"):format(libraryfx, os.date("%X %x"), namefx, stringfx)
				local ke_path = debug.getinfo(1, "S").source
				local folfer = ke_path:match("(.*/)") or ke_path:match("(.*\\)")
				local path = folfer .. "newkara_fxlist.lua"
				local fxlines = {}
				for l in io.lines(path) do
					table.insert(fxlines, l)
				end
				table.insert(fxlines, #fxlines + 1, newfx)
				fxfile = io.open(path, "w") --write
				for _, l in ipairs(fxlines) do
					fxfile:write(l .. "\n")
				end
				fxfile:close()
				namefx = namefx:gsub("_", " ")
				local debugout = ("The effect [%s] has been saved successfully, you must reload the script Effector2 so you can see it in the list effects."):format(namefx)
				aegisub.debug.out(debugout)
			end,
			
			modifyline = function(fx__, meta, line, ke)
				fx__.fx_return = ke.tag.tonumber(fx__.fx_return)
				local tovalue = ("return function(fx__, meta, line, ke) return %s end"):format(fx__.fx_return)
				local returnfx = line.text
				if pcall(loadstring(tovalue)) then
					returnfx = loadstring(tovalue)()(fx__, meta, line, ke) or returnfx
				end
				--return ke.tag.dark(returnfx)
				return returnfx
			end, --ke.config.modifyline(fx__, meta, orgline, ke)
			
			upgradefx = function(str)
				local arrayfx = ke.string.toval("{" .. str:match("effector.create_fx(%b())"):sub(2, -2) .. "}")
				local index = {1, 2, 3, 12, 13, 21, 22, 27, 29, 24, 25, 26, 6, 7, 8, 9, 10, 11, 31, 30, 5, 4}
				local names = {"fx_folder", "fx_namefx", "fx_type", "fx_start", "fx_end", "fx_layer", "fx_align", "fx_loop",
					"fx_return", "fx_posx", "fx_posy", "fx_time", "fx_color1", "fx_color3", "fx_color4", "fx_alpha1",
					"fx_alpha3", "fx_alpha4", "fx_variable", "fx_addtags", "fx_reverse", "fx_noblank", "fx_vertical"
				}
				local temps = {LIfx = "leadinfx", HLfx = "hilightfx", LOfx = "leadoutfx", SHfx = "shapefx", TLfx = "translationfx"}
				local upfx = {}
				for i, idx in ipairs(index) do
					local key = names[i]
					upfx[key] = arrayfx[idx]
				end
				upfx.fx_vertical = false
				upfx.fx_folder = temps[upfx.fx_folder]
				return ke.config.temp.fx_to_string(upfx)
			end,
			
			debugging = function()
				local test = include("kelibs\\functions.lua")
				return test(ke)
			end,
		},
		
	}
	
	return ke