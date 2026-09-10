/* Copyright (C) 2026 Qore Technologies, s.r.o. */

import java.io.BufferedReader;
import java.io.InputStreamReader;
import java.nio.charset.StandardCharsets;
import javax.xml.datatype.DatatypeFactory;
import javax.xml.datatype.XMLGregorianCalendar;

/** Independent decimal-precision value comparisons, separate from Xerces schema validation. */
public final class TemporalValueOracle {
    private TemporalValueOracle() {
    }

    public static void main(String[] args) throws Exception {
        DatatypeFactory factory = DatatypeFactory.newDefaultInstance();
        try (BufferedReader input = new BufferedReader(new InputStreamReader(System.in, StandardCharsets.UTF_8))) {
            String line;
            while ((line = input.readLine()) != null) {
                String[] fields = line.split("\t", -1);
                if (fields.length != 3) {
                    throw new IllegalArgumentException("expected identity, left and right lexical values");
                }
                XMLGregorianCalendar left = factory.newXMLGregorianCalendar(fields[1]);
                XMLGregorianCalendar right = factory.newXMLGregorianCalendar(fields[2]);
                System.out.println(fields[0] + "\t" + left.compare(right) + "\t"
                    + left.normalize().toXMLFormat() + "\t" + right.normalize().toXMLFormat());
            }
        }
    }
}
