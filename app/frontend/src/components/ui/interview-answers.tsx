import { AnimatePresence, motion, Variants } from "framer-motion";

import { InterviewItem } from "@/types";

import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./card";
import { useRef } from "react";
// import { useTranslation } from "react-i18next";

import { Check } from "lucide-react";

type Properties = {
    answers?: InterviewItem;
    isSuccess?: boolean;
};

const variants: Variants = {
    hidden: { opacity: 0, scale: 0.8, y: 20 },
    visible: (i: number) => ({
        opacity: 1,
        scale: 1,
        y: 0,
        transition: {
            delay: i * 0.1,
            duration: 0.3,
            type: "spring",
            stiffness: 300,
            damping: 20
        }
    })
};

const propertyNamesMap: Record<string, string> = {
    name: "Nome",
    cpf: "CPF",
    category: "Categoria",
    expirationDate: "Data de Expiração",
};


export function InterviewAnswers({ answers, isSuccess }: Properties) {
    // const { t } = useTranslation();
    const isAnimating = useRef(false);

    if (!answers) {
        return null;
    }

    return (
        <Card className="m-4 max-w-full md:max-w-md lg:min-w-96 lg:max-w-2xl">
            <CardHeader>
                <CardTitle className="flex flex-row items-center place-content-between text-xl">
                    Dados do usuário
                    {isSuccess && <Check className="flex h-5 text-green-500 w-5" />}
                    </CardTitle>
                <CardDescription>
                  Dados do usuário com base na entrevista.
                </CardDescription>
            </CardHeader>
            <CardContent>
                <AnimatePresence>
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: "auto" }}
                        exit={{ opacity: 0, height: 0 }}
                        transition={{ duration: 0.3 }}
                        className={`h-full ${isAnimating ? "overflow-hidden" : "overflow-y-auto"}`}
                        onLayoutAnimationStart={() => (isAnimating.current = true)}
                        onLayoutAnimationComplete={() => (isAnimating.current = false)}
                    >
                        <div className="flex flex-col gap-2">
                            {Object.entries(answers)
                                .filter(([_, value]) => value) // Exibe apenas os campos preenchidos
                                .map(([key, value], index) => (
                                    <motion.div
                                        key={index}
                                        variants={variants}
                                        initial="hidden"
                                        animate="visible"
                                        custom={index}
                                    >
                                        <strong>{propertyNamesMap[key] || key}:</strong> {value.includes("\"") ? (<span className="opacity-70">{value}</span>) : (value)}
                                    </motion.div>
                                ))}
                        </div>
                    </motion.div>
                </AnimatePresence>
                <span className="opacity-60 text-sm text-red-700">Estes são os dados que serão de fato enviados.</span>
            </CardContent>
        </Card>
    );
}
