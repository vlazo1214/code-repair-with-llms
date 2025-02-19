/*
 * Copyright 1999-2101 Alibaba Group.
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */
package com.alibaba.fastjson.serializer;

import java.io.IOException;
import java.lang.reflect.Array;
import java.lang.reflect.GenericArrayType;
import java.lang.reflect.ParameterizedType;
import java.lang.reflect.Type;
import java.lang.reflect.TypeVariable;
import java.util.IdentityHashMap;

import com.alibaba.fastjson.JSONArray;
import com.alibaba.fastjson.JSONException;
import com.alibaba.fastjson.parser.DefaultJSONParser;
import com.alibaba.fastjson.parser.JSONLexer;
import com.alibaba.fastjson.parser.JSONToken;
import com.alibaba.fastjson.parser.deserializer.ObjectDeserializer;
import com.alibaba.fastjson.util.TypeUtils;

/**
 * Author: wenshao[szujobs@hotmail.com]
 */
public class ObjectArrayCodec implements ObjectSerializer, ObjectDeserializer {

    public static final ObjectArrayCodec instance = new ObjectArrayCodec();

    public ObjectArrayCodec() {}

    public final void write(JSONSerializer serializer, Object object, Object fieldName, Type fieldType, int features) throws IOException {
        SerializeWriter out = serializer.out;

        Object[] array = (Object[]) object;

        if (object == null) {
            out.writeNull(SerializerFeature.WriteNullListAsEmpty);
            return;
        }

        int size = array.length;
        int end = size - 1;

        if (end == -1) {
            out.append("[]");
            return;
        }

        SerialContext context = serializer.context;
        serializer.setContext(context, object, fieldName, 0);

        try {
            Class<?> preClazz = null;
            ObjectSerializer preWriter = null;
            out.append('[');

            if (out.isEnabled(SerializerFeature.PrettyFormat)) {
                serializer.incrementIndent();
                serializer.println();
                for (int i = 0; i < size; ++i) {
                    if (i != 0) {
                        out.write(',');
                        serializer.println();
                    }
                    serializer.write(array[i]);
                }
                serializer.decrementIdent();
                serializer.println();
                out.write(']');
                return;
            }

            for (int i = 0; i < end; ++i) {
                Object item = array[i];

                if (item == null) {
                    out.append("null,");
                } else {
                    if (serializer.containsReference(item)) {
                        serializer.writeReference(item);
                    } else {
                        Class<?> clazz = item.getClass();

                        if (clazz == preClazz) {
                            preWriter.write(serializer, item, null, null, 0);
                        } else {
                            preClazz = clazz;
                            preWriter = serializer.getObjectWriter(clazz);
                            preWriter.write(serializer, item, null, null, 0);
                        }
                    }
                    out.append(',');
                }
            }

            Object item = array[end];

            if (item == null) {
                out.append("null]");
            } else {
                if (serializer.containsReference(item)) {
                    serializer.writeReference(item);
                } else {
                    serializer.writeWithFieldName(item, end);
                }
                out.append(']');
            }
        } finally {
            serializer.context = context;
        }
    }
    
    @SuppressWarnings({ "unchecked", "rawtypes" })
    public <T> T deserialze(DefaultJSONParser parser, Type type, Object fieldName) {
        final JSONLexer lexer = parser.lexer;
        if (lexer.token() == JSONToken.NULL) {
            lexer.nextToken(JSONToken.COMMA);
            return null;
        }

        if (lexer.token() == JSONToken.LITERAL_STRING) {
            byte[] bytes = lexer.bytesValue();
            lexer.nextToken(JSONToken.COMMA);
            return (T) bytes;
        }

        Class componentClass;
        Type componentType;
        if (type instanceof GenericArrayType) {
            GenericArrayType clazz = (GenericArrayType) type;
            componentType = clazz.getGenericComponentType();
            if (componentType instanceof TypeVariable) {
                TypeVariable typeVar = (TypeVariable) componentType;
                Type objType = parser.getContext().type;
                if (objType instanceof ParameterizedType) {
                    ParameterizedType objParamType = (ParameterizedType) objType;
                    Type objRawType = objParamType.getRawType();
                    Type actualType = null;
                    if (objRawType instanceof Class) {
                        TypeVariable[] objTypeParams = ((Class) objRawType).getTypeParameters();
                        for (int i = 0; i < objTypeParams.length; ++i) {
                            if (objTypeParams[i].getName().equals(typeVar.getName())) {
                                actualType = objParamType.getActualTypeArguments()[i];
                            }
                        }
                    }
                    if (actualType instanceof Class) {
                        componentClass = (Class) actualType;
                    } else {
                        componentClass = Object.class;
                    }
                } else {
                    componentClass = TypeUtils.getClass(typeVar.getBounds()[0]);
                }
            } else {
                componentClass = TypeUtils.getClass(componentType);
            }
        } else {
            Class clazz = (Class) type;
            componentType = componentClass = clazz.getComponentType();
        }
        JSONArray array = new JSONArray();
        parser.parseArray(componentClass, array, fieldName);

        return (T) toObjectArray(parser, componentClass, array);
    }

    @SuppressWarnings("unchecked")
    private <T> T toObjectArray(DefaultJSONParser parser, Class<?> componentType, JSONArray array) {
        return toObjectArray(parser, componentType, array, new IdentityHashMap<>());
    }

    @SuppressWarnings("unchecked")
    private <T> T toObjectArray(DefaultJSONParser parser, Class<?> componentType, JSONArray array, IdentityHashMap<JSONArray, Object> visited) {
        if (array == null) {
            return null;
        }

        if (visited.containsKey(array)) {
            return (T) Array.newInstance(componentType, 0); // Or handle circular dependency as needed
        }

        int size = array.size();
        Object objArray = Array.newInstance(componentType, size);
        visited.put(array, objArray);

        for (int i = 0; i < size; ++i) {
            Object value = array.get(i);
            if (componentType.isArray()) {
                Object element;
                if (value instanceof JSONArray) {
                    JSONArray jsonArray = (JSONArray) value;
                    element = componentType.isInstance(value) ? value : toObjectArray(parser, componentType, jsonArray, visited);
                } else {
                    element = value;
                }
                Array.set(objArray, i, element);
            } else {
                Object element = (value instanceof JSONArray) ? ((JSONArray) value).toArray() : TypeUtils.cast(value, componentType, parser.getConfig());
                Array.set(objArray, i, element);
            }
        }
        return (T) objArray;
    }

    public int getFastMatchToken() {
        return JSONToken.LBRACKET;
    }
}
